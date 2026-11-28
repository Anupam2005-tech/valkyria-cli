"""
First-run setup wizard — interactive onboarding matching §4.1 of the spec.

Guides the user through:
1. Optional Firebase Google OAuth browser handoff (or local-only mode)
2. Encrypted vault setup / remote sync pull & provider API key entry
3. Live credential validation and model catalog discovery
4. Optional user profile (name, profession, expertise — never languages/tone)
5. Role-based model assignments + separate embeddings mode
6. Review screen with privacy summary -> save only after confirmation
"""

from __future__ import annotations

import asyncio

import click
from rich.panel import Panel
from rich.table import Table

from valkyrie.auth.tokens import AuthUser, get_valid_user
from valkyrie.core.config import (
    ModelAssignment,
    ProviderConfig,
    UserProfile,
    ValkyrieConfig,
)
from valkyrie.core.console import (
    console,
    print_banner,
    print_error,
    print_info,
    print_kv,
    print_rule,
    print_success,
    print_warning,
)
from valkyrie.providers.base import ModelCapability, ModelInfo
from valkyrie.providers.registry import ModelRegistry, get_provider
from valkyrie.vault.prompt import prompt_master_password, verify_and_prompt
from valkyrie.vault.store import (
    SUPPORTED_PROVIDERS,
    add_key,
    get_key,
    get_vault_blob,
    save_vault_blob,
    vault_exists,
)
from valkyrie.vault.sync import pull_vault, push_vault

_CORE_ROLES = ["chat", "code", "planner", "vision", "summarization"]
_EXPERTISE_CHOICES = ["beginner", "intermediate", "advanced", "skip"]


def _step_auth() -> AuthUser | None:
    """Step 1: Check Firebase auth and explain browser handoff if signed out."""
    print_rule("Step 1 of 5 · Account")
    console.print()

    user = get_valid_user()
    if user is not None:
        print_success(f"Signed in as [bold]{user.email}[/bold]")
        console.print()
        return user

    print_info(
        "Valkyrie uses Firebase Google sign-in (via a local browser handoff) "
        "to back up your encrypted key vault."
    )
    print_info("You can also run locally without signing in and log in later.")
    console.print()

    if click.confirm("  Sign in with Google now?", default=False):
        from valkyrie.cli.auth_commands import login

        ctx = click.get_current_context(silent=True)
        if ctx is not None:
            ctx.invoke(login)
        else:
            login.callback()  # type: ignore[misc]
        user = get_valid_user()
    else:
        print_info("Skipping sign-in. Continuing in local-only mode.")

    console.print()
    return user


def _maybe_pull_remote_vault(user: AuthUser | None) -> None:
    """If signed in and no local vault exists, offer to pull from Firebase."""
    if user is None or vault_exists():
        return

    print_info("Checking Firebase for an existing encrypted vault...")
    blob = pull_vault(user.id_token, user.uid)
    if blob is None:
        return

    if click.confirm("  Found a synced vault in Firebase. Download it?", default=True):
        save_vault_blob(blob)
        print_success("Remote vault downloaded. You'll unlock it with your master password.")
        console.print()


def _unlock_or_create_password() -> str | None:
    """Unlock an existing vault or create a new master password."""
    if vault_exists():
        return verify_and_prompt(action="unlock your key vault")
    return prompt_master_password(confirm_new=True)


def _collect_provider_keys(password: str) -> dict[str, str]:
    """Prompt for provider selection and masked API keys, validating live."""
    existing_keys: dict[str, str] = {}
    for pkey in SUPPORTED_PROVIDERS:
        found = get_key(password, pkey)
        if found:
            existing_keys[pkey] = found

    if existing_keys:
        names = ", ".join(SUPPORTED_PROVIDERS[p]["name"] for p in existing_keys)
        print_info(f"Existing keys found in vault: [bold]{names}[/bold]")
        if not click.confirm("  Add or update another provider key?", default=False):
            return existing_keys

    print_info("Available hosted providers:")
    console.print()
    for pid, pinfo in SUPPORTED_PROVIDERS.items():
        status = "[green]configured[/green]" if pid in existing_keys else "[dim]not set[/dim]"
        console.print(f"    [accent]{pid:<10}[/accent] {pinfo['description']:<32} {status}")
    console.print()

    while True:
        choice = click.prompt(
            "  Select provider to configure (or 'done')",
            type=click.Choice([*SUPPORTED_PROVIDERS.keys(), "done"], case_sensitive=False),
            default="done" if existing_keys else "groq",
        ).lower()

        if choice == "done":
            if not existing_keys:
                print_warning("At least one hosted provider is required for chat.")
                continue
            break

        pinfo = SUPPORTED_PROVIDERS[choice]
        print_info(f"Get your {pinfo['name']} key at: [dim]{pinfo['url']}[/dim]")
        raw_key = click.prompt(
            f"  {pinfo['name']} API key",
            hide_input=True,
            prompt_suffix=": ",
        ).strip()

        if not raw_key:
            print_error("API key cannot be empty.")
            continue

        provider = get_provider(choice)
        if provider is not None:
            print_info(f"Validating {pinfo['name']} credentials...")
            valid = asyncio.run(provider.validate_key(raw_key))
            if not valid:
                print_error(f"{pinfo['name']} rejected this key or was unreachable.")
                if not click.confirm("  Save anyway?", default=False):
                    continue

        add_key(password, choice, raw_key)
        existing_keys[choice] = raw_key
        print_success(f"{pinfo['name']} key stored in encrypted vault.")
        console.print()

        if not click.confirm("  Connect another provider?", default=False):
            break

    return existing_keys


def _step_providers_and_discovery(
    user: AuthUser | None,
) -> tuple[str | None, dict[str, str], ModelRegistry]:
    """Step 2: Vault unlock/creation, key entry, and model catalog discovery."""
    print_rule("Step 2 of 5 · Providers & Models")
    console.print()

    _maybe_pull_remote_vault(user)

    password = _unlock_or_create_password()
    if password is None:
        return None, {}, ModelRegistry.load_cache()

    api_keys = _collect_provider_keys(password)
    if not api_keys:
        return password, {}, ModelRegistry.load_cache()

    print_info("Fetching model catalogs...")
    registry = ModelRegistry.load_cache()
    summary = asyncio.run(registry.refresh(api_keys))

    console.print()
    for pkey, (valid, count) in summary.items():
        pname = SUPPORTED_PROVIDERS[pkey]["name"]
        if valid:
            print_success(f"{pname:<15} {count} models available")
        else:
            print_warning(f"{pname:<15} could not fetch catalog (cached data preserved)")

    _print_capability_summary(registry)
    console.print()
    return password, api_keys, registry


def _print_capability_summary(registry: ModelRegistry) -> None:
    """Group discovered models by capability and show counts."""
    if not registry.models:
        return

    console.print()
    for cap in ModelCapability:
        matches = registry.list_models(capability=cap)
        if matches:
            sample = ", ".join(m.qualified_id for m in matches[:3])
            suffix = f" (+{len(matches) - 3} more)" if len(matches) > 3 else ""
            print_kv(cap.value, f"[dim]{sample}{suffix}[/dim]")


def _step_profile(user: AuthUser | None, existing: UserProfile) -> UserProfile:
    """Step 3: Optional user profile (never asks for languages or tone)."""
    print_rule("Step 3 of 5 · Profile (Optional)")
    console.print()
    print_info("All fields are optional. Press Enter to skip any question.")
    console.print()

    default_name = existing.name or (user.display_name if user else None) or ""
    name = click.prompt("  Preferred name", default=default_name, show_default=bool(default_name))
    profession = click.prompt(
        "  Profession",
        default=existing.profession or "",
        show_default=bool(existing.profession),
    )
    expertise = click.prompt(
        "  Expertise level",
        type=click.Choice(_EXPERTISE_CHOICES, case_sensitive=False),
        default=existing.expertise or "skip",
    ).lower()

    console.print()
    return UserProfile(
        name=name.strip() or None,
        profession=profession.strip() or None,
        expertise=None if expertise == "skip" else expertise,
    )


def _prompt_role_model(
    role: str,
    candidates: list[ModelInfo],
    current: str | None,
    *,
    required: bool = False,
) -> str | None:
    """Prompt user to pick a compatible model for a role, with provider filtering."""
    if not candidates:
        print_info(f"Role [bold]{role}[/bold]: no compatible models discovered -> unassigned")
        return None

    active_filter: str | None = None
    while True:
        visible = (
            [m for m in candidates if m.provider == active_filter]
            if active_filter
            else candidates
        )
        shown = visible[:10]
        filter_label = f" · filter={active_filter}" if active_filter else ""
        console.print(
            f"  [heading]{role.upper()}[/heading]  "
            f"[muted]({len(visible)} compatible{filter_label})[/muted]"
        )
        for idx, m in enumerate(shown, start=1):
            ctx = f"{m.context_window // 1000}k" if m.context_window else "unknown ctx"
            console.print(
                f"    [accent]{idx:>2}[/accent]  [model]{m.qualified_id}[/model] [dim]({ctx})[/dim]"
            )
        if len(visible) > len(shown):
            more = len(visible) - len(shown)
            console.print(
                f"    [dim]... +{more} more. Type a provider name (groq/gemini/nvidia) "
                "to filter, or enter <provider>/<model>.[/dim]"
            )
        if not required:
            console.print("     [accent]0[/accent]  [muted]unassigned[/muted]")

        default_val = "1" if (required or current is None) else current
        raw = click.prompt(f"  Select {role} model", default=default_val).strip()
        lower_raw = raw.lower()
        if lower_raw in ("all", "*"):
            active_filter = None
            console.print()
            continue
        if lower_raw in {m.provider for m in candidates}:
            active_filter = lower_raw
            console.print()
            continue
        if raw == "0" or lower_raw == "unassigned":
            if required:
                print_warning(f"Role '{role}' requires a model.")
                continue
            return None
        if raw.isdigit():
            pos = int(raw) - 1
            if 0 <= pos < len(shown):
                return shown[pos].qualified_id
        match = next((m for m in candidates if m.qualified_id == raw), None)
        if match is not None:
            return match.qualified_id
        print_error(
            "Invalid selection. Enter a number, provider name to filter, or provider/model."
        )


def _step_assignments(
    registry: ModelRegistry,
    existing_models: ModelAssignment,
    existing_embedding_mode: str,
) -> tuple[ModelAssignment, str]:
    """Step 4: Assign compatible models to roles and configure Pinecone embeddings."""
    print_rule("Step 4 of 5 · Role Assignments")
    console.print()

    assignments = ModelAssignment()
    for role in _CORE_ROLES:
        candidates = registry.list_models(role=role)
        current = getattr(existing_models, role, None)
        selected = _prompt_role_model(
            role,
            candidates,
            current,
            required=(role == "chat" and bool(candidates)),
        )
        setattr(assignments, role, selected)
        console.print()

    print_info("RAG vectors & chunks are stored exclusively in Pinecone DB (never locally).")
    print_info(
        "[dim]pinecone[/dim] uses Pinecone Inference / hash vectors; "
        "[dim]hosted[/dim] uses an explicit provider embedding model."
    )
    embed_candidates = registry.list_models(role="embeddings")
    choices = ["pinecone", "unassigned"]
    if embed_candidates:
        choices.insert(1, "hosted")

    embedding_mode = click.prompt(
        "  Embeddings mode",
        type=click.Choice(choices, case_sensitive=False),
        default=existing_embedding_mode if existing_embedding_mode in choices else "pinecone",
    ).lower()

    if embedding_mode == "hosted":
        assignments.embeddings = _prompt_role_model(
            "embeddings",
            embed_candidates,
            existing_models.embeddings,
            required=True,
        )
    else:
        assignments.embeddings = None

    console.print()
    return assignments, embedding_mode


def _step_review_and_save(
    config: ValkyrieConfig,
    user: AuthUser | None,
    password: str | None,
) -> bool:
    """Step 5: Show review screen with privacy summary; save only after confirmation."""
    print_rule("Step 5 of 5 · Review & Confirm")
    console.print()

    table = Table(border_style="rule", show_header=False, pad_edge=False)
    table.add_column("Setting", style="key", width=20)
    table.add_column("Value", style="value")

    auth_str = user.email if user else "local-only (not signed in)"
    providers_str = ", ".join(config.providers.keys()) or "none"
    table.add_row("Account", auth_str)
    table.add_row("Providers", providers_str)
    table.add_row("Chat model", config.models.chat or "unassigned")
    table.add_row("Code model", config.models.code or "unassigned")
    table.add_row("Planner model", config.models.planner or "unassigned")
    table.add_row("Vision model", config.models.vision or "unassigned")
    table.add_row("Summarization", config.models.summarization or "unassigned")
    embed_display = (
        f"hosted ({config.models.embeddings})"
        if config.embedding_mode == "hosted" and config.models.embeddings
        else config.embedding_mode
    )
    table.add_row("Embeddings", embed_display)
    table.add_row("Vault sync", "enabled" if config.sync_enabled else "disabled")
    console.print(table)
    console.print()

    privacy_lines = [
        "• Prompts and attached context are sent only to the hosted provider you invoke.",
        "• API keys remain encrypted locally with AES-256-GCM (master password never stored).",
    ]
    if config.embedding_mode == "hosted" and config.models.embeddings:
        privacy_lines.append(
            f"• RAG Storage: Pinecone DB ({config.pinecone.index_name}) "
            f"with hosted embeddings ({config.models.embeddings})."
        )
    elif config.embedding_mode == "unassigned":
        privacy_lines.append("• RAG indexing is unassigned (Pinecone not enabled).")
    else:
        privacy_lines.append(
            f"• RAG Storage: Pinecone DB only ({config.pinecone.index_name}) "
            "— zero local vector storage."
        )
    if config.sync_enabled:
        privacy_lines.append(
            "• Sync enabled: only your opaque encrypted vault blob is uploaded to Firebase."
        )

    console.print(
        Panel(
            "\n".join(privacy_lines),
            title="[heading]Privacy Summary[/heading]",
            border_style="rule",
        )
    )
    console.print()

    if not click.confirm("  Save this configuration?", default=True):
        print_warning("Setup cancelled. Nothing was saved.")
        console.print()
        return False

    config.first_run_complete = True
    saved_path = config.save()
    print_success(f"Configuration saved to [dim]{saved_path}[/dim]")

    if config.sync_enabled and user is not None and password is not None:
        blob = get_vault_blob()
        if blob and push_vault(user.id_token, user.uid, blob):
            print_success("Encrypted vault synced to Firebase.")
        else:
            print_warning(
                "Vault sync could not complete right now. Run 'valkyrie keys sync' later."
            )

    console.print()
    print_info("Ready. Try inspecting your catalog: [bold]valkyrie model list[/bold]")
    console.print()
    return True


def run_setup_wizard() -> bool:
    """Run the complete first-run setup flow. Returns True if configuration was saved."""
    print_banner()
    console.print()

    existing = ValkyrieConfig.load()
    user = _step_auth()
    password, api_keys, registry = _step_providers_and_discovery(user)
    if password is None:
        print_error("Setup requires unlocking or creating your vault.")
        console.print()
        return False

    profile = _step_profile(user, existing.profile)
    models, embedding_mode = _step_assignments(
        registry,
        existing.models,
        existing.embedding_mode,
    )

    sync_enabled = False
    if user is not None:
        sync_enabled = click.confirm(
            "  Automatically sync encrypted key vault to Firebase?",
            default=existing.sync_enabled or True,
        )
        console.print()

    providers_cfg = {
        pkey: ProviderConfig(name=SUPPORTED_PROVIDERS[pkey]["name"], enabled=True)
        for pkey in api_keys
        if pkey in SUPPORTED_PROVIDERS
    }

    new_config = ValkyrieConfig(
        version=existing.version,
        first_run_complete=True,
        profile=profile,
        models=models,
        providers=providers_cfg,
        embedding_mode=embedding_mode,
        sync_enabled=sync_enabled,
        feature_flags=existing.feature_flags,
    )

    return _step_review_and_save(new_config, user, password)


@click.command()
def setup() -> None:
    """Run the interactive setup wizard."""
    run_setup_wizard()

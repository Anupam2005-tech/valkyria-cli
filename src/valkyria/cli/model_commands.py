"""
Model CLI commands — inspect catalogs, filter by provider, refresh live, and assign roles.
"""

from __future__ import annotations

import asyncio

import click
from rich import box
from rich.table import Table
from rich.text import Text

from valkyria.core.config import ProviderConfig, ValkyriaConfig
from valkyria.core.console import (
    console,
    print_error,
    print_info,
    print_kv,
    print_rule,
    print_success,
    print_warning,
)
from valkyria.providers.base import ASSIGNABLE_ROLES, ModelCapability, ModelInfo
from valkyria.providers.registry import PROVIDERS, ModelRegistry


def _format_ctx(ctx: int | None) -> str:
    """Format context window token count, or 'unknown' if missing."""
    if ctx is None:
        return "unknown"
    if ctx >= 1_000_000:
        return f"{ctx / 1_000_000:.1f}M"
    if ctx >= 1_000:
        return f"{ctx // 1_000}k"
    return str(ctx)


def _render_provider_filter_bar(
    registry: ModelRegistry,
    active_provider: str | None,
) -> None:
    """Render an editorial provider pill bar showing available providers to filter by."""
    counts = registry.provider_counts()
    total = sum(counts.values())
    bar = Text("  PROVIDERS  ", style="grey62")

    if active_provider is None:
        bar.append(f" ALL ({total}) ", style="bold black on bright_cyan")
    else:
        bar.append(f"ALL ({total})", style="grey62")

    for pkey in PROVIDERS:
        cnt = counts.get(pkey, 0)
        bar.append("  ·  ", style="grey35")
        if active_provider == pkey:
            bar.append(f" {pkey.upper()} ({cnt}) ", style="bold black on bright_cyan")
        elif cnt > 0:
            bar.append(f"{pkey} ({cnt})", style="bright_white")
        else:
            bar.append(f"{pkey} (0)", style="grey42")

    console.print(bar)
    console.print(
        "  [muted]Tip: filter anytime with [bold]--provider <name>[/bold] "
        "or in chat with [bold]/model <provider>[/bold].[/muted]"
    )
    console.print()


@click.group(invoke_without_command=True)
@click.pass_context
def model(ctx: click.Context) -> None:
    """Inspect available models and manage role assignments."""
    if ctx.invoked_subcommand is not None:
        return

    config = ValkyriaConfig.load()
    registry = ModelRegistry.load_cache()

    console.print()
    print_rule("Model Assignments")
    console.print()

    for role in ASSIGNABLE_ROLES:
        assigned = getattr(config.models, role, None)
        display = f"[model]{assigned}[/model]" if assigned else "[muted]unassigned[/muted]"
        print_kv(role, display)

    console.print()
    cached_count = len(registry.models)
    if cached_count > 0:
        counts = registry.provider_counts()
        breakdown = " · ".join(f"{k}: {v}" for k, v in counts.items())
        print_info(
            f"Catalog: [bold]{cached_count}[/bold] models ([dim]{breakdown}[/dim])."
        )
    else:
        print_info(
            "No cached models yet. Run [bold]valkyria model refresh[/bold] to fetch catalogs."
        )
    console.print()


@model.command(name="list")
@click.option(
    "-p",
    "--provider",
    type=click.Choice(list(PROVIDERS.keys()), case_sensitive=False),
    default=None,
    help="Filter models to a specific provider (groq, gemini, nvidia).",
)
@click.option(
    "-r",
    "--role",
    type=click.Choice(ASSIGNABLE_ROLES, case_sensitive=False),
    default=None,
    help="Only show models compatible with a role.",
)
@click.option(
    "-c",
    "--capability",
    type=click.Choice([c.value for c in ModelCapability], case_sensitive=False),
    default=None,
    help="Filter by capability.",
)
@click.option(
    "-s",
    "--search",
    default=None,
    help="Filter models by name/ID substring.",
)
def list_cmd(
    provider: str | None,
    role: str | None,
    capability: str | None,
    search: str | None,
) -> None:
    """List models available under configured keys, optionally filtered by provider."""
    registry = ModelRegistry.load_cache()
    config = ValkyriaConfig.load()

    console.print()
    print_rule("Model Catalog")
    console.print()

    if not registry.models:
        print_info("No cached models found.")
        print_info("Run [bold]valkyria model refresh[/bold] after adding a provider key.")
        console.print()
        return

    selected_provider = provider.lower() if provider else None
    _render_provider_filter_bar(registry, selected_provider)

    cap_enum = ModelCapability(capability.lower()) if capability else None
    models = registry.list_models(
        provider=selected_provider,
        capability=cap_enum,
        role=role.lower() if role else None,
        search=search,
    )

    if not models:
        print_warning("No models match the selected filters.")
        console.print()
        return

    grouped: dict[str, list[ModelInfo]] = {}
    for m in models:
        grouped.setdefault(m.provider, []).append(m)

    for pkey, items in grouped.items():
        p_obj = PROVIDERS.get(pkey)
        pname = p_obj.name if p_obj else pkey
        table = Table(
            title=f"[heading]◆ {pname}[/heading] [muted]({len(items)})[/muted]",
            title_justify="left",
            box=box.ROUNDED,
            border_style="rule",
            header_style="bold bright_white",
            show_lines=False,
            pad_edge=True,
        )
        table.add_column("#", style="grey50", justify="right", width=3)
        table.add_column("Model", style="model", no_wrap=(console.width >= 78))
        table.add_column("Capabilities", style="bright_cyan")
        table.add_column("Ctx", justify="right", style="dim")
        table.add_column("State", justify="right")

        for idx, m in enumerate(items, start=1):
            caps_str = " · ".join(c.value for c in m.capabilities) or "unknown"
            ctx_str = _format_ctx(m.context_window)
            if m.qualified_id == config.models.chat:
                state_str = "[tag] DEFAULT [/tag]"
            elif m.is_active:
                state_str = "[success]ready[/success]"
            else:
                state_str = "[warning]retired[/warning]"
            table.add_row(str(idx), m.qualified_id, caps_str, ctx_str, state_str)

        console.print(table)
        console.print()


@model.command()
@click.option(
    "-p",
    "--provider",
    type=click.Choice(list(PROVIDERS.keys()), case_sensitive=False),
    default=None,
    help="Refresh only a specific provider.",
)
def refresh(provider: str | None) -> None:
    """Validate keys and fetch live model catalogs from providers."""
    from valkyria.vault.prompt import verify_and_prompt
    from valkyria.vault.store import get_key, vault_exists

    console.print()
    print_rule("Refresh Model Catalog")
    console.print()

    if not vault_exists():
        print_error("No key vault found. Run [bold]valkyria keys add[/bold] first.")
        console.print()
        return

    password = verify_and_prompt(action="unlock API keys")
    if password is None:
        console.print()
        return

    target_providers = [provider.lower()] if provider else list(PROVIDERS.keys())
    api_keys: dict[str, str] = {}
    for pkey in target_providers:
        key = get_key(password, pkey)
        if key:
            api_keys[pkey] = key

    if not api_keys:
        print_warning("No matching API keys found in vault.")
        console.print()
        return

    print_info(f"Querying {len(api_keys)} provider(s)...")
    registry = ModelRegistry.load_cache()
    summary = asyncio.run(registry.refresh(api_keys))

    config = ValkyriaConfig.load()
    console.print()
    for pkey, (valid, count) in summary.items():
        p_obj = PROVIDERS[pkey]
        if valid:
            print_success(f"{p_obj.name:<15} {count} models discovered")
            config.providers[pkey] = ProviderConfig(name=p_obj.name, enabled=True)
        else:
            print_error(f"{p_obj.name:<15} key validation failed or unreachable")

    config.save()
    console.print()


@model.command(name="set")
@click.argument("role", type=click.Choice(ASSIGNABLE_ROLES, case_sensitive=False))
@click.argument("model_id")
def set_cmd(role: str, model_id: str) -> None:
    """Assign a model (provider/model or unique model ID) to a role, or 'unassigned' to clear."""
    role = role.lower()
    config = ValkyriaConfig.load()

    console.print()
    print_rule("Set Role Assignment")
    console.print()

    if model_id.lower() == "unassigned":
        setattr(config.models, role, None)
        config.save()
        print_success(f"Role [bold]{role}[/bold] cleared (unassigned).")
        console.print()
        return

    registry = ModelRegistry.load_cache()
    resolved_id = model_id

    if "/" not in model_id and registry.models:
        found, suggestions = registry.resolve_model(model_id)
        if found is None:
            print_error(f"Could not resolve '{model_id}' to a unique model.")
            if suggestions:
                print_info("Matches: " + ", ".join(m.qualified_id for m in suggestions[:5]))
            console.print()
            raise SystemExit(1)
        resolved_id = found.qualified_id

    if "/" not in resolved_id:
        print_error(
            "Model must be specified as <provider>/<model_id> "
            "(e.g. groq/llama-3.3-70b-versatile)."
        )
        console.print()
        raise SystemExit(1)

    provider_key, _ = resolved_id.split("/", 1)
    if provider_key not in PROVIDERS:
        print_error(f"Unknown provider '{provider_key}'. Supported: {', '.join(PROVIDERS.keys())}.")
        console.print()
        raise SystemExit(1)

    if registry.models:
        model_info = registry.get_model(resolved_id)
        if model_info is None:
            print_error(f"Model '{resolved_id}' not found in cached catalog.")
            print_info(
                "Run [bold]valkyria model list[/bold] to inspect available models, "
                "or [bold]valkyria model refresh[/bold]."
            )
            console.print()
            raise SystemExit(1)

        if not model_info.supports_role(role):
            compatible = registry.list_models(role=role)
            print_error(f"Model '{resolved_id}' does not support role '{role}'.")
            if compatible:
                suggestions_txt = ", ".join(m.qualified_id for m in compatible[:5])
                print_info(f"Compatible models: {suggestions_txt}")
            console.print()
            raise SystemExit(1)
    else:
        print_warning("No cached catalog found; saving assignment without capability check.")

    setattr(config.models, role, resolved_id)
    config.save()
    print_success(f"Assigned [model]{resolved_id}[/model] to [bold]{role}[/bold].")
    console.print()

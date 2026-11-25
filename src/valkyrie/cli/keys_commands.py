"""
Keys CLI commands — manage provider API keys in the encrypted vault.
"""

import click

from valkyrie.core.console import (
    console,
    print_error,
    print_info,
    print_rule,
    print_success,
    print_warning,
)
from valkyrie.vault.store import SERVICE_KEYS, SUPPORTED_PROVIDERS


@click.group()
def keys() -> None:
    """Manage provider API keys."""
    pass


@keys.command()
@click.argument("provider", required=False)
def add(provider: str | None) -> None:
    """Add or update an API key for a provider."""
    from valkyrie.vault.prompt import prompt_master_password
    from valkyrie.vault.store import add_key

    console.print()
    print_rule("Add Provider Key")
    console.print()

    # If no provider specified, show options
    if provider is None:
        print_info("Available services:")
        console.print()
        for pid, pinfo in SERVICE_KEYS.items():
            console.print(f"    [accent]{pid:<10}[/accent] {pinfo['description']}")
        console.print()
        provider = click.prompt("  Service", type=click.Choice(list(SERVICE_KEYS.keys())))

    provider = provider.lower()
    if provider not in SERVICE_KEYS:
        print_error(f"Unknown service: {provider}")
        print_info(f"Supported: {', '.join(SERVICE_KEYS.keys())}")
        raise SystemExit(1)

    pinfo = SERVICE_KEYS[provider]
    console.print()
    print_info(f"Adding key for [accent]{pinfo['name']}[/accent]")
    print_info(f"Get your key at: [dim]{pinfo['url']}[/dim]")
    console.print()

    # Get the master password (create vault if first time)
    password = prompt_master_password()
    if password is None:
        return

    # Get the API key (masked input)
    api_key = click.prompt(
        f"  {pinfo['name']} API key",
        hide_input=True,
        prompt_suffix=": ",
    )

    if not api_key.strip():
        print_error("API key cannot be empty.")
        return

    # Validate key format hint (non-blocking)
    expected_prefix = pinfo.get("prefix", "")
    if expected_prefix and not api_key.startswith(expected_prefix):
        print_warning(
            f"Key doesn't start with '{expected_prefix}'. "
            f"It may still work — saving anyway."
        )

    # Store it
    add_key(password, provider, api_key.strip())

    # Record model provider in config (skip vector DB entries like pinecone)
    if provider in SUPPORTED_PROVIDERS:
        from valkyrie.core.config import ProviderConfig, ValkyrieConfig

        config = ValkyrieConfig.load()
        config.providers[provider] = ProviderConfig(name=pinfo["name"], enabled=True)
        config.save()

    console.print()
    print_success(f"{pinfo['name']} key saved to encrypted vault.")
    if provider in SUPPORTED_PROVIDERS:
        print_info("Run [bold]valkyrie model refresh[/bold] to discover available models.")

    # Offer to sync
    _offer_sync(password)

    console.print()


@keys.command(name="list")
def list_cmd() -> None:
    """List stored provider keys (masked)."""
    from valkyrie.vault.store import vault_exists

    console.print()
    print_rule("Provider Keys")
    console.print()

    if not vault_exists():
        print_info("No vault found. Run [bold]valkyrie keys add[/bold] to add your first key.")
        console.print()
        return

    from valkyrie.vault.prompt import verify_and_prompt
    from valkyrie.vault.store import list_keys

    password = verify_and_prompt(action="list your keys")
    if password is None:
        console.print()
        return

    stored_keys = list_keys(password)

    if not stored_keys:
        print_info("Vault is empty. Run [bold]valkyrie keys add[/bold] to add a key.")
    else:
        console.print()
        for provider, data in stored_keys.items():
            pinfo = SERVICE_KEYS.get(provider, {"name": provider})
            name = pinfo["name"] if isinstance(pinfo, dict) else provider
            console.print(f"    [accent]{name:<18}[/accent] [dim]{data['masked_key']}[/dim]")

    console.print()


@keys.command()
@click.argument("provider")
def remove(provider: str) -> None:
    """Remove a provider key from the vault."""
    from valkyrie.vault.store import vault_exists

    provider = provider.lower()

    console.print()
    print_rule("Remove Key")
    console.print()

    if not vault_exists():
        print_error("No vault found.")
        console.print()
        return

    if provider not in SERVICE_KEYS:
        print_warning(f"Unknown service '{provider}', checking vault anyway.")

    pinfo = SERVICE_KEYS.get(provider, {"name": provider})
    name = pinfo["name"] if isinstance(pinfo, dict) else provider

    if not click.confirm(f"  Remove {name} key?", default=False):
        print_info("Cancelled.")
        console.print()
        return

    from valkyrie.vault.prompt import verify_and_prompt
    from valkyrie.vault.store import remove_key

    password = verify_and_prompt(action="remove a key")
    if password is None:
        console.print()
        return

    if remove_key(password, provider):
        from valkyrie.core.config import ValkyrieConfig

        config = ValkyrieConfig.load()
        config.providers.pop(provider, None)
        config.save()
        print_success(f"{name} key removed.")
        _offer_sync(password)
    else:
        print_info(f"No key found for {name}.")

    console.print()


@keys.command()
def sync() -> None:
    """Sync the encrypted vault to/from Firebase."""
    from valkyrie.vault.store import vault_exists

    console.print()
    print_rule("Vault Sync")
    console.print()

    if not vault_exists():
        # Try pulling from remote
        _pull_from_remote()
        return

    from valkyrie.vault.prompt import verify_and_prompt

    password = verify_and_prompt(action="sync your vault")
    if password is None:
        console.print()
        return

    _do_sync(password)
    console.print()


# ── Sync helpers ────────────────────────────────────────────────────────────


def _offer_sync(password: str) -> None:
    """Offer to sync after a vault change."""
    from valkyrie.auth.tokens import get_valid_user

    user = get_valid_user()
    if user is None:
        return

    if click.confirm("\n  Sync vault to Firebase?", default=True):
        _do_sync(password)


def _do_sync(password: str) -> None:
    """Push local vault to Firebase."""
    from valkyrie.auth.tokens import get_valid_user
    from valkyrie.vault.store import get_vault_blob
    from valkyrie.vault.sync import push_vault

    user = get_valid_user()
    if user is None:
        print_warning("Not signed in. Sign in first to sync.")
        return

    blob = get_vault_blob()
    if blob is None:
        print_info("No vault to sync.")
        return

    print_info("Pushing encrypted vault to Firebase...")
    if push_vault(user.id_token, user.uid, blob):
        print_success("Vault synced to Firebase.")
    else:
        print_error("Sync failed. Check your connection and try again.")


def _pull_from_remote() -> None:
    """Pull vault from Firebase when no local vault exists."""
    from valkyrie.auth.tokens import get_valid_user
    from valkyrie.vault.store import save_vault_blob
    from valkyrie.vault.sync import pull_vault

    user = get_valid_user()
    if user is None:
        print_info("Not signed in. Run [bold]valkyrie auth login[/bold] first.")
        console.print()
        return

    print_info("No local vault. Checking Firebase for a synced vault...")
    blob = pull_vault(user.id_token, user.uid)

    if blob is None:
        print_info(
            "No remote vault found either. Run [bold]valkyrie keys add[/bold] to create one."
        )
    else:
        save_vault_blob(blob)
        print_success("Vault downloaded from Firebase. Unlock it with your master password.")

    console.print()


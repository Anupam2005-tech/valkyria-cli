"""
Shared account lifecycle operations — login, switch, logout, status, and deletion.

Used by both the `valkyrie auth` CLI commands and the in-chat `/account` slash command.
"""

from __future__ import annotations

import time
import webbrowser

import click

from valkyrie.auth.firebase_config import OAUTH_CALLBACK_HOST, OAUTH_CALLBACK_PORT
from valkyrie.auth.server import run_auth_server
from valkyrie.auth.tokens import (
    AuthUser,
    clear_auth,
    delete_firebase_account,
    get_valid_user,
    load_auth,
    save_auth,
)
from valkyrie.core.config import ValkyrieConfig
from valkyrie.core.console import (
    console,
    print_error,
    print_info,
    print_kv,
    print_rule,
    print_success,
    print_warning,
)
from valkyrie.core.paths import get_vault_path
from valkyrie.vault.store import save_vault_blob, vault_exists
from valkyrie.vault.sync import delete_remote_vault, pull_vault


def _run_browser_oauth(*, select_account: bool = False) -> AuthUser | None:
    """Open the browser OAuth flow, wait for callback, and persist tokens."""
    login_url = f"http://{OAUTH_CALLBACK_HOST}:{OAUTH_CALLBACK_PORT}/"
    print_info("Opening your browser for Google sign-in.")
    print_info(f"If it doesn't open, visit: [accent]{login_url}[/accent]")
    print_info("[dim]Waiting for authentication...[/dim]")
    console.print()

    webbrowser.open(login_url)
    result = run_auth_server(timeout=300.0, select_account=select_account)
    if result is None:
        print_error("Authentication timed out or was cancelled.")
        return None

    user = AuthUser.from_oauth_callback(result)
    save_auth(user)
    return user


def login_account(*, select_account: bool = False) -> AuthUser | None:
    """Sign in via browser OAuth if not already signed in."""
    existing = get_valid_user()
    if existing is not None:
        console.print()
        print_info(f"Already signed in as [bold]{existing.email}[/bold].")
        print_info(
            "Run [bold]/account switch[/bold] or [bold]valkyrie auth switch[/bold] "
            "to change accounts."
        )
        console.print()
        return existing

    console.print()
    print_rule("Sign In")
    console.print()
    user = _run_browser_oauth(select_account=select_account)
    if user is None:
        return None

    print_success(f"Signed in as [bold]{user.email}[/bold]")
    if user.display_name:
        print_info(f"Welcome, {user.display_name}.")
    console.print()
    return user


def switch_account(*, interactive: bool = True) -> AuthUser | None:
    """
    Switch to a different Google account via Firebase OAuth account chooser.

    Preserves the currently signed-in session if the browser flow is cancelled.
    """
    previous = load_auth()
    console.print()
    print_rule("Switch Account")
    console.print()
    if previous is not None:
        print_info(f"Currently signed in as [bold]{previous.email}[/bold].")
    else:
        print_info("Not currently signed in — opening account selector.")

    new_user = _run_browser_oauth(select_account=True)
    if new_user is None:
        if previous is not None:
            print_info(f"Kept existing session ([bold]{previous.email}[/bold]).")
        console.print()
        return None

    print_success(f"Switched account -> [bold]{new_user.email}[/bold]")
    if new_user.display_name:
        print_info(f"Signed in as {new_user.display_name} ([dim]{new_user.uid}[/dim]).")

    remote_blob = pull_vault(new_user.id_token, new_user.uid)
    if remote_blob is not None:
        should_pull = True if not interactive else click.confirm(
            f"  Synced vault found for {new_user.email}. Replace local vault with synced vault?",
            default=False,
        )
        if should_pull:
            save_vault_blob(remote_blob)
            cfg = ValkyrieConfig.load()
            cfg.sync_enabled = True
            cfg.save()
            print_success("Pulled encrypted vault for switched account.")
        else:
            print_info("Kept current local vault.")
    console.print()
    return new_user


def logout_account() -> bool:
    """Sign out locally and clear ~/.valkyrie/auth.json."""
    user = load_auth()
    if user is None:
        console.print()
        print_info("Not signed in.")
        console.print()
        return False

    email = user.email
    clear_auth()
    console.print()
    print_success(f"Signed out from [bold]{email}[/bold].")
    print_info("Local credentials cleared.")
    console.print()
    return True


def delete_account(*, assume_yes: bool = False, purge_local: bool = False) -> bool:
    """
    Permanently delete the signed-in Firebase account and its remote Firestore vault.

    Clears local auth credentials and optionally deletes the local encrypted vault.
    """
    user = get_valid_user()
    if user is None:
        stale = load_auth()
        console.print()
        if stale is not None:
            print_error(
                "Stored authentication token expired and could not be refreshed. "
                "Run '/account switch' (or 'valkyrie auth switch') to re-authenticate first."
            )
        else:
            print_info("Not signed in. No account to delete.")
        console.print()
        return False

    console.print()
    print_rule("Delete Account")
    console.print()
    print_warning(
        f"This permanently deletes Firebase account [bold]{user.email}[/bold] "
        f"([dim]{user.uid}[/dim]) and any synced remote vault."
    )

    if not assume_yes and not click.confirm(
        f"  Permanently delete account '{user.email}'?",
        default=False,
    ):
        print_info("Account deletion cancelled.")
        console.print()
        return False

    remote_ok = delete_remote_vault(user.id_token, user.uid)
    if not remote_ok:
        print_warning("Could not verify remote vault deletion (continuing with account removal).")

    ok, detail = delete_firebase_account(user.id_token)
    if not ok:
        print_error(detail)
        console.print()
        return False

    clear_auth()
    cfg = ValkyrieConfig.load()
    cfg.sync_enabled = False
    cfg.save()

    vault_path = get_vault_path()
    should_purge = purge_local
    if not should_purge and not assume_yes and vault_exists():
        should_purge = click.confirm(
            f"  Also delete local encrypted key vault ({vault_path})?",
            default=False,
        )
    if should_purge and vault_path.exists():
        vault_path.unlink()
        print_info("Local encrypted vault removed.")

    print_success(f"Deleted account [bold]{user.email}[/bold] and cleared local credentials.")
    console.print()
    return True


def show_account_status() -> None:
    """Display active signed-in account, token status, and vault sync state."""
    user = load_auth()
    cfg = ValkyrieConfig.load()

    console.print()
    print_rule("Authentication")
    console.print()

    if user is None:
        print_kv("Status", "[yellow]not signed in[/yellow]")
        print_kv("Sync", "disabled (local-only mode)")
        print_info(
            "Run [bold]/account login[/bold] or [bold]valkyrie auth login[/bold] to sign in."
        )
    else:
        expired = user.is_expired
        status_str = "[red]token expired[/red]" if expired else "[green]active[/green]"
        print_kv("Status", status_str)
        print_kv("Email", f"[bold]{user.email}[/bold]")
        if user.display_name:
            print_kv("Name", user.display_name)
        print_kv("UID", f"[dim]{user.uid}[/dim]")
        print_kv("Cloud sync", "enabled" if cfg.sync_enabled else "disabled")
        if not expired:
            remaining = int(user.expires_at - time.time())
            minutes = remaining // 60
            print_kv("Token", f"expires in {minutes} min")
        else:
            print_info("Token will refresh automatically on next use.")

    console.print()

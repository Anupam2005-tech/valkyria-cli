"""
Auth CLI commands — login, switch, delete, logout, and status.
"""

import click

from valkyria.auth.account import (
    delete_account,
    login_account,
    logout_account,
    show_account_status,
    switch_account,
)


@click.group()
def auth() -> None:
    """Manage authentication and account lifecycle."""
    pass


@auth.command()
def login() -> None:
    """Sign in with Google via browser handoff."""
    user = login_account(select_account=False)
    if user is None:
        raise SystemExit(1)


@auth.command()
def switch() -> None:
    """Switch to another Google account via browser selector."""
    user = switch_account(interactive=True)
    if user is None:
        raise SystemExit(1)


@auth.command()
@click.option("--yes", is_flag=True, help="Skip confirmation prompts.")
@click.option(
    "--purge-local",
    is_flag=True,
    help="Also delete the local encrypted key vault (vault.enc).",
)
def delete(yes: bool, purge_local: bool) -> None:
    """Permanently delete the signed-in account and remote synced vault."""
    if not delete_account(assume_yes=yes, purge_local=purge_local):
        raise SystemExit(1)


@auth.command()
def logout() -> None:
    """Sign out and clear stored credentials."""
    logout_account()


@auth.command(name="status")
def auth_status() -> None:
    """Show current authentication state."""
    show_account_status()


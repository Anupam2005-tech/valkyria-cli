"""
Master password prompt — secure input for vault operations.

Handles first-time password creation (with confirmation) and subsequent
unlock prompts. Never echoes the password to the terminal.
"""

from __future__ import annotations

import click

from valkyria.core.console import console, print_error, print_info, print_warning
from valkyria.vault.store import vault_exists


def prompt_master_password(*, confirm_new: bool = True) -> str | None:
    """
    Prompt the user for the master password.

    If the vault doesn't exist and confirm_new is True, asks for confirmation.
    Returns the password string or None if the user cancelled.
    """
    is_new = not vault_exists()

    if is_new:
        console.print()
        print_info("Setting up your encrypted vault.")
        print_info("Choose a master password to protect your API keys.")
        print_warning("This password is never stored. If you forget it, keys must be re-entered.")
        console.print()

        password = click.prompt(
            "  Master password",
            hide_input=True,
            confirmation_prompt=confirm_new,
            prompt_suffix=": ",
        )
    else:
        password = click.prompt(
            "  Master password",
            hide_input=True,
            prompt_suffix=": ",
        )

    if not password or len(password) < 4:
        print_error("Password must be at least 4 characters.")
        return None

    return password


def verify_and_prompt(*, action: str = "access your keys") -> str | None:
    """
    Prompt for the master password and verify it against the existing vault.

    Returns the password if correct, None if cancelled or wrong.
    """
    from cryptography.exceptions import InvalidTag

    from valkyria.vault.store import load_vault

    password = click.prompt(
        "  Master password",
        hide_input=True,
        prompt_suffix=": ",
    )

    try:
        load_vault(password)
        return password
    except FileNotFoundError:
        print_error("No vault found.")
        return None
    except InvalidTag:
        print_error("Wrong password.")
        return None


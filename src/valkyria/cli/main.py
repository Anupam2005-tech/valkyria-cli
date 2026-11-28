"""
Valkyrie CLI — main entry point.

This module defines the root Click command group and wires up all subcommands.
"""

import sys

import click

from valkyrie import __version__
from valkyrie.core.console import console, print_banner, print_info, print_warning

_CLI_ALIASES = {
    "c": "chat",
    "m": "model",
    "k": "keys",
    "a": "auth",
    "r": "rag",
    "s": "status",
    "ss": "session",
    "in": "login",
    "out": "logout",
}


class _AliasedGroup(click.Group):
    """Click group supporting short aliases and unambiguous command prefixes."""

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv
        mapped = _CLI_ALIASES.get(cmd_name.lower())
        if mapped:
            return super().get_command(ctx, mapped)
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name.lower())]
        if len(matches) == 1:
            return super().get_command(ctx, matches[0])
        return None


@click.group(cls=_AliasedGroup, invoke_without_command=True)
@click.version_option(__version__, prog_name="valkyrie")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Valkyrie — a precise, fast terminal AI workspace."""
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        from valkyrie.auth.tokens import load_auth
        from valkyrie.core.config import ValkyrieConfig

        config = ValkyrieConfig.load()
        if config.is_first_run and sys.stdin.isatty():
            from valkyrie.cli.setup_wizard import run_setup_wizard

            run_setup_wizard()
            return

        print_banner()

        if config.is_first_run:
            print_warning(
                "First-run setup is incomplete. Run [bold]valkyrie setup[/bold] to configure."
            )
        else:
            user = load_auth()
            if user is None:
                print_info(
                    "Running in local-only mode. Run [bold]valkyrie login[/bold] to enable sync."
                )
            else:
                print_info(f"Signed in as [bold]{user.email}[/bold]")

        console.print(
            "\n  Type [bold]valkyrie --help[/bold] to see available commands.\n",
            style="dim",
        )


@cli.command()
def status() -> None:
    """Show current authentication and configuration status."""
    from valkyrie.auth.tokens import load_auth
    from valkyrie.core.config import ValkyrieConfig
    from valkyrie.core.paths import get_config_dir

    config_dir = get_config_dir()
    config = ValkyrieConfig.load()
    user = load_auth()

    from valkyrie.core.console import print_kv, print_rule

    console.print()
    print_rule("Status")
    console.print()
    print_kv("Config directory", f"[dim]{config_dir}[/dim]")

    if user is not None:
        print_kv("Auth", f"[green]{user.email}[/green]")
    else:
        print_kv("Auth", "[yellow]not signed in[/yellow]")

    provider_count = len(config.providers)
    if provider_count > 0:
        print_kv("Providers", f"[green]{provider_count} configured[/green]")
    else:
        print_kv("Providers", "[yellow]none[/yellow]")

    assignments = config.models
    assigned = sum(
        1
        for v in [
            assignments.chat,
            assignments.code,
            assignments.planner,
            assignments.vision,
            assignments.summarization,
        ]
        if v is not None
    )
    print_kv("Model roles", f"[dim]{assigned}/5 assigned[/dim]")

    first_run_str = (
        "[yellow]pending[/yellow]" if config.is_first_run else "[green]complete[/green]"
    )
    print_kv("First run", first_run_str)

    from valkyrie.core.paths import get_sessions_db_path
    from valkyrie.core.workspace import detect_workspace_root

    ws_root = detect_workspace_root()
    print_kv("Workspace", f"[dim]{ws_root}[/dim]")
    print_kv("Vector DB", f"Pinecone ({config.pinecone.index_name})")

    if get_sessions_db_path().exists():
        from valkyrie.sessions.store import SessionStore

        latest = SessionStore().get_latest_session(workspace_root=str(ws_root))
        if latest is not None:
            print_kv(
                "Latest session",
                f"[green]{latest.id}[/green] [dim]({latest.title})[/dim]",
            )
        else:
            print_kv("Latest session", "[yellow]none in workspace[/yellow]")
    else:
        print_kv("Active session", "[yellow]none[/yellow]")
    console.print()


# ── Register subcommand groups ──────────────────────────────────────────────

from valkyrie.cli.auth_commands import auth, login, logout  # noqa: E402
from valkyrie.cli.chat_commands import chat  # noqa: E402
from valkyrie.cli.keys_commands import keys  # noqa: E402
from valkyrie.cli.model_commands import model  # noqa: E402
from valkyrie.cli.rag_commands import rag  # noqa: E402
from valkyrie.cli.session_commands import session  # noqa: E402
from valkyrie.cli.setup_wizard import setup  # noqa: E402

cli.add_command(auth)
cli.add_command(chat)
cli.add_command(keys)
cli.add_command(model)
cli.add_command(rag)
cli.add_command(session)
cli.add_command(setup)
cli.add_command(login)
cli.add_command(logout)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

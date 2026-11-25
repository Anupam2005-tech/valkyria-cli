"""
Session CLI commands — list, create, inspect, rename, fork, search, compact, delete.
"""

from __future__ import annotations

import click
from rich.table import Table

from valkyrie.chat.engine import build_system_prompt
from valkyrie.chat.messages import ChatMessage, MessageRole
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
from valkyrie.core.workspace import detect_workspace_root
from valkyrie.sessions.store import SessionStore


def _build_extractive_summary(messages: list[ChatMessage], keep_last: int) -> str:
    """Create a deterministic local summary of older turns when no LLM is invoked."""
    non_system = [m for m in messages if m.role != MessageRole.SYSTEM]
    older = non_system[:-keep_last] if keep_last > 0 else non_system
    bullets: list[str] = []
    for msg in older:
        snippet = " ".join(msg.content.split())
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        bullets.append(f"- {msg.role.value}: {snippet}")
    return "\n".join(bullets)


@click.group()
def session() -> None:
    """Manage durable conversation sessions."""
    pass


@session.command(name="list")
@click.option("--all", "show_all", is_flag=True, help="List sessions across all workspaces.")
def list_cmd(show_all: bool) -> None:
    """List saved sessions."""
    store = SessionStore()
    ws = None if show_all else str(detect_workspace_root())
    sessions = store.list_sessions(workspace_root=ws)

    console.print()
    print_rule("Sessions")
    console.print()

    if not sessions:
        print_info("No sessions found. Start one with [bold]valkyrie chat[/bold].")
        console.print()
        return

    table = Table(border_style="rule", header_style="bold white", pad_edge=False)
    table.add_column("ID", style="accent", no_wrap=True)
    table.add_column("Title", style="body")
    table.add_column("Model", style="model")
    table.add_column("Msgs", justify="right", style="dim")
    table.add_column("Updated", style="dim", no_wrap=True)

    for s in sessions:
        table.add_row(
            s.id,
            s.title[:40],
            s.active_model,
            str(s.message_count),
            s.updated_at[:16].replace("T", " "),
        )

    console.print(table)
    console.print()


@session.command()
@click.option("--title", default=None, help="Optional session title.")
@click.option("--model", "model_id", default=None, help="Override chat model for this session.")
def new(title: str | None, model_id: str | None) -> None:
    """Create a new persistent session."""
    config = ValkyrieConfig.load()
    selected = model_id or config.models.chat or "unassigned"
    store = SessionStore()
    sys_msg = ChatMessage(role=MessageRole.SYSTEM, content=build_system_prompt(config))
    created = store.create_session(
        active_model=selected,
        workspace_root=str(detect_workspace_root()),
        title=title,
        initial_messages=[sys_msg],
    )

    console.print()
    print_success(f"Created session [bold]{created.title}[/bold] ([dim]{created.id}[/dim])")
    print_info(f"Resume with: [bold]valkyrie chat --session {created.id}[/bold]")
    console.print()


@session.command()
@click.argument("session_id")
def show(session_id: str) -> None:
    """Show metadata and recent messages for a session."""
    store = SessionStore()
    sess = store.get_session(session_id)

    console.print()
    if sess is None:
        print_error(f"Session '{session_id}' not found.")
        console.print()
        raise SystemExit(1)

    print_rule(f"Session · {sess.id}")
    console.print()
    print_kv("Title", sess.title)
    print_kv("Workspace", sess.workspace_root)
    print_kv("Model", f"[model]{sess.active_model}[/model]")
    print_kv("Messages", str(sess.message_count))
    print_kv(
        "Tokens",
        f"{sess.total_prompt_tokens:,} in · {sess.total_completion_tokens:,} out",
    )
    if sess.last_checkpoint_id:
        print_kv("Checkpoint", sess.last_checkpoint_id)
    console.print()

    msgs = [m for m in store.load_messages(sess.id) if m.role != MessageRole.SYSTEM]
    for msg in msgs[-10:]:
        snippet = msg.content if len(msg.content) <= 200 else msg.content[:197] + "..."
        console.print(f"  [accent]{msg.role.value:<10}[/accent] {snippet}")
    if msgs:
        console.print()


@session.command()
@click.argument("session_id")
@click.argument("title")
def rename(session_id: str, title: str) -> None:
    """Rename a saved session."""
    store = SessionStore()
    console.print()
    if store.rename_session(session_id, title):
        print_success(f"Renamed session to [bold]{title}[/bold].")
    else:
        print_error(f"Session '{session_id}' not found.")
        console.print()
        raise SystemExit(1)
    console.print()


@session.command()
@click.argument("session_id")
@click.option("--title", default=None, help="Title for the forked session.")
def fork(session_id: str, title: str | None) -> None:
    """Fork an existing session into a new branch."""
    store = SessionStore()
    forked = store.fork_session(session_id, title=title)
    console.print()
    if forked is None:
        print_error(f"Session '{session_id}' not found.")
        console.print()
        raise SystemExit(1)
    print_success(f"Forked into [bold]{forked.title}[/bold] ([dim]{forked.id}[/dim])")
    console.print()


@session.command()
@click.argument("query")
def search(query: str) -> None:
    """Search sessions by title or message content."""
    store = SessionStore()
    matches = store.search_sessions(query)
    console.print()
    print_rule(f"Search · {query}")
    console.print()

    if not matches:
        print_info("No matching sessions found.")
        console.print()
        return

    for s in matches:
        console.print(
            f"  [accent]{s.id}[/accent]  [bold]{s.title}[/bold]  "
            f"[dim]({s.message_count} msgs · {s.active_model})[/dim]"
        )
    console.print()


@session.command()
@click.argument("session_id")
@click.option(
    "--keep",
    default=4,
    show_default=True,
    help="Number of recent messages to keep verbatim.",
)
def compact(session_id: str, keep: int) -> None:
    """Compact older messages in a session into a summary."""
    store = SessionStore()
    sess = store.get_session(session_id)
    console.print()
    if sess is None:
        print_error(f"Session '{session_id}' not found.")
        console.print()
        raise SystemExit(1)

    messages = store.load_messages(sess.id)
    summary = _build_extractive_summary(messages, keep)
    ok, before_cnt, after_cnt = store.compact_session(sess.id, summary, keep_last=keep)

    if ok:
        print_success(
            f"Compacted session [dim]{sess.id}[/dim]: {before_cnt} -> {after_cnt} messages."
        )
    else:
        print_warning("Session has too few messages to compact.")
    console.print()


@session.command()
@click.argument("session_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def delete(session_id: str, yes: bool) -> None:
    """Delete a saved session."""
    store = SessionStore()
    sess = store.get_session(session_id)
    console.print()
    if sess is None:
        print_error(f"Session '{session_id}' not found.")
        console.print()
        raise SystemExit(1)

    if not yes and not click.confirm(
        f"  Delete session '{sess.title}' ({sess.id})?", default=False
    ):
        print_info("Cancelled.")
        console.print()
        return

    store.delete_session(sess.id)
    print_success(f"Deleted session [dim]{sess.id}[/dim].")
    console.print()

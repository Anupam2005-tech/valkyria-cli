"""
Compact tool action cards — left-accented Rich panels for workspace & provider clarity.
"""

from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.text import Text

from valkyria.core.console import console


def render_tool_card(
    *,
    tool: str,
    status: str,
    target: str,
    summary: str,
    details: str | None = None,
) -> None:
    """
    Render a sharp editorial action card with semantic left border accents.

    Args:
        tool: Tool label (e.g. 'read', 'index', 'search', 'rag', 'provider')
        status: 'ok', 'blocked', or 'error'
        target: Target file path, directory, model, or query
        summary: Single-line summary of operation/effect
        details: Optional multi-line snippet or citation details
    """
    status_style, border_style, badge = {
        "ok": ("bold bright_green", "cyan", "OK"),
        "blocked": ("bold bright_yellow", "yellow", "BLOCKED"),
        "error": ("bold bright_red", "red", "ERROR"),
    }.get(status, ("bold bright_cyan", "cyan", status.upper()))

    body = Text()
    body.append(f" {badge} ", style=f"{status_style} reverse")
    body.append("  ")
    body.append(target, style="bold bright_white")
    body.append(f"\n{summary}", style="grey70")
    if details:
        body.append(f"\n\n{details}", style="white")

    console.print(
        Panel(
            body,
            box=box.ROUNDED,
            title=f"[heading]◆ {tool.upper()}[/heading]",
            title_align="left",
            border_style=border_style,
            padding=(0, 1),
        )
    )

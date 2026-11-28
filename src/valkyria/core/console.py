"""
Console and theme — sharp editorial terminal design.

A restrained obsidian/slate grid, electric cyan functional accent, confident typography,
and zero decorative fluff. Adapts gracefully to narrow terminals (< 80 columns).
"""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# ── Editorial terminal palette ──────────────────────────────────────────────
VALKYRIA_THEME = Theme(
    {
        # Core hierarchy
        "title": "bold bright_white",
        "subtitle": "dim white",
        "heading": "bold bright_cyan",
        "body": "white",
        "dim": "dim white",
        "muted": "grey62",
        # Status
        "success": "bold bright_green",
        "warning": "bold bright_yellow",
        "error": "bold bright_red",
        "info": "bright_cyan",
        # Accent — electric cyan & subtle chrome
        "accent": "bold bright_cyan",
        "accent.dim": "cyan",
        # UI elements
        "rule": "grey35",
        "prompt": "bold bright_white",
        "prompt.arrow": "bright_cyan",
        "key": "bold white",
        "value": "white",
        "tag": "bold black on bright_cyan",
        "tag.dim": "bold bright_cyan",
        # Model & provider
        "model": "bold bright_magenta",
        "provider": "bold bright_blue",
        # Code
        "code": "bright_white on grey11",
    }
)

# ── Shared console instance ────────────────────────────────────────────────
console = Console(theme=VALKYRIA_THEME, highlight=False)


def render_meter(ratio: float, *, width: int = 12) -> str:
    """Render a compact visual meter bar using block glyphs."""
    clamped = max(0.0, min(1.0, ratio))
    filled = round(clamped * width)
    empty = width - filled
    bar_color = (
        "bright_red"
        if clamped >= 0.85
        else ("bright_yellow" if clamped >= 0.65 else "bright_cyan")
    )
    return f"[{bar_color}]{'█' * filled}[/{bar_color}][grey30]{'░' * empty}[/grey30]"


def print_banner() -> None:
    """Print the Valkyria editorial masthead, adaptive to terminal width."""
    from valkyria import __version__

    console.print()
    header = Text()
    header.append("◆ ", style="bold bright_cyan")
    header.append("VALKYRIA", style="bold bright_white")
    header.append(f"  v{__version__}", style="grey62")
    if console.width >= 64:
        header.append("   ·   ", style="grey35")
        header.append("TERMINAL-FIRST AI WORKSPACE", style="bold bright_cyan")
    header.append("\n")
    header.append("  Sharp mind. Crisp edges. Zero fluff.", style="italic grey70")

    console.print(
        Panel(
            header,
            box=box.ROUNDED,
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )


def print_rule(title: str = "") -> None:
    """Print a sharp horizontal rule with optional section label."""
    if title:
        console.rule(f" [heading]◆ {title}[/heading] ", style="rule")
    else:
        console.rule(style="rule")


def print_success(msg: str) -> None:
    """Print a success message."""
    console.print(f"  [success]◆[/success] {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    console.print(f"  [warning]▲[/warning] {msg}")


def print_error(msg: str) -> None:
    """Print an error message."""
    console.print(f"  [error]✕[/error] {msg}")


def print_info(msg: str) -> None:
    """Print an info message."""
    console.print(f"  [info]▸[/info] {msg}")


def print_kv(key: str, value: str, indent: int = 2) -> None:
    """Print a key-value pair with consistent editorial alignment."""
    pad = " " * indent
    key_w = 14 if console.width < 72 else 20
    console.print(f"{pad}[muted]{key:<{key_w}}[/muted] [value]{value}[/value]")

"""
Streaming Markdown renderer — live thinking indicator, Markdown streaming, and tool capture.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

from valkyrie.chat.messages import TokenUsage, estimate_messages_tokens, estimate_tokens
from valkyrie.core.console import console

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from valkyrie.chat.clients import StreamChunk, ToolCall
    from valkyrie.chat.messages import ChatMessage


async def render_agent_stream(
    chunks: AsyncIterator[StreamChunk],
    *,
    qualified_model: str,
    prompt_messages: list[ChatMessage],
) -> tuple[str, TokenUsage, list[ToolCall]]:
    """
    Stream chunks to the terminal as live-rendered Markdown, collecting any tool calls.

    Returns (full_response_text, token_usage, tool_calls).
    """
    provider, _, model_name = qualified_model.partition("/")
    header = Text()
    header.append("  ┃ ", style="bright_cyan")
    header.append("◆ ", style="bold bright_magenta")
    if model_name:
        header.append(f"{provider}", style="bold bright_blue")
        header.append("/", style="grey50")
        header.append(model_name, style="bold bright_magenta")
    else:
        header.append(qualified_model, style="bold bright_magenta")
    header.append("  ·  ", style="grey42")
    header.append("hosted stream", style="grey62")

    console.print()
    console.print(header)

    buffer: list[str] = []
    tool_calls: list[ToolCall] = []
    final_usage: TokenUsage | None = None
    started_at = time.perf_counter()

    spinner = Spinner(
        "dots",
        text=Text(" routing & thinking…", style="grey62"),
        style="bright_cyan",
    )
    with Live(
        spinner,
        console=console,
        refresh_per_second=14,
        transient=False,
    ) as live:
        async for chunk in chunks:
            if chunk.delta:
                buffer.append(chunk.delta)
                live.update(Markdown("".join(buffer)))
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
            if chunk.usage is not None:
                final_usage = chunk.usage

        full_text = "".join(buffer)
        if not full_text and tool_calls:
            names = ", ".join(tc.name for tc in tool_calls)
            live.update(Text(f"  ▸ invoking tools: {names}", style="bright_cyan"))
        elif not full_text:
            live.update(Text("  (empty response)", style="muted"))

    elapsed = max(0.01, time.perf_counter() - started_at)

    if final_usage is None:
        final_usage = TokenUsage(
            prompt_tokens=estimate_messages_tokens(prompt_messages),
            completion_tokens=estimate_tokens(full_text),
            estimated=True,
        )

    approx = "~" if final_usage.estimated else ""
    tps = final_usage.completion_tokens / elapsed if final_usage.completion_tokens > 0 else 0.0
    tps_part = f" · {tps:.0f} tok/s" if tps >= 1.0 else ""

    footer = Text()
    footer.append("  └─ ", style="grey35")
    footer.append(
        f"{approx}{final_usage.prompt_tokens:,} in · "
        f"{approx}{final_usage.completion_tokens:,} out · "
        f"{elapsed:.2f}s{tps_part}",
        style="grey62",
    )
    console.print(footer)
    console.print()
    return full_text, final_usage, tool_calls


async def render_stream(
    chunks: AsyncIterator[StreamChunk],
    *,
    qualified_model: str,
    prompt_messages: list[ChatMessage],
) -> tuple[str, TokenUsage]:
    """Stream text response without returning tool_calls (backwards-compatible wrapper)."""
    text, usage, _ = await render_agent_stream(
        chunks,
        qualified_model=qualified_model,
        prompt_messages=prompt_messages,
    )
    return text, usage

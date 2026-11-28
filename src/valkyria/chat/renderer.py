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

from valkyria.chat.messages import TokenUsage, estimate_messages_tokens, estimate_tokens
from valkyria.core.console import console

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from valkyria.chat.clients import StreamChunk, ToolCall
    from valkyria.chat.messages import ChatMessage


def _print_stream_header(qualified_model: str, phase: str = "hosted stream") -> None:
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
    header.append(phase, style="grey62")

    console.print()
    console.print(header)


def _print_stream_footer(usage: TokenUsage, elapsed: float) -> None:
    approx = "~" if usage.estimated else ""
    tps = usage.completion_tokens / elapsed if usage.completion_tokens > 0 else 0.0
    tps_part = f" · {tps:.0f} tok/s" if tps >= 1.0 else ""

    footer = Text()
    footer.append("  └─ ", style="grey35")
    footer.append(
        f"{approx}{usage.prompt_tokens:,} in · "
        f"{approx}{usage.completion_tokens:,} out · "
        f"{elapsed:.2f}s{tps_part}",
        style="grey62",
    )
    console.print(footer)
    console.print()


class NodeStreamRenderer:
    """Manages Rich Live Markdown rendering for a single LangGraph LLM node invocation."""

    def __init__(
        self,
        *,
        qualified_model: str,
        phase: str = "hosted stream",
        prompt_messages: list[ChatMessage] | None = None,
    ) -> None:
        self.qualified_model = qualified_model
        self.phase = phase
        self.prompt_messages = prompt_messages or []
        self.buffer: list[str] = []
        self.usage: TokenUsage | None = None
        self._live: Live | None = None
        self._started_at = time.perf_counter()

    def start(self) -> None:
        """Print the stream header and start the live Rich spinner."""
        _print_stream_header(self.qualified_model, phase=self.phase)
        self._started_at = time.perf_counter()
        spinner = Spinner(
            "dots",
            text=Text(" routing & thinking…", style="grey62"),
            style="bright_cyan",
        )
        self._live = Live(
            spinner,
            console=console,
            refresh_per_second=14,
            transient=False,
        )
        self._live.__enter__()

    def feed(self, delta: str, usage: TokenUsage | None = None) -> None:
        """Append streamed token text and refresh Live Markdown."""
        if self._live is None:
            self.start()
        if delta:
            self.buffer.append(delta)
            if self._live is not None:
                self._live.update(Markdown("".join(self.buffer)))
        if usage is not None:
            self.usage = usage

    def finish(
        self,
        *,
        tool_names: list[str] | None = None,
        fallback_usage: TokenUsage | None = None,
    ) -> tuple[str, TokenUsage]:
        """Stop Live display, print token footer, and return (full_text, usage)."""
        full_text = "".join(self.buffer)
        if self._live is not None:
            if not full_text and tool_names:
                self._live.update(
                    Text(f"  ▸ invoking tools: {', '.join(tool_names)}", style="bright_cyan")
                )
            elif not full_text:
                self._live.update(Text("  (empty response)", style="muted"))
            self._live.__exit__(None, None, None)
            self._live = None

        elapsed = max(0.01, time.perf_counter() - self._started_at)
        final_usage = self.usage or fallback_usage
        if final_usage is None:
            final_usage = TokenUsage(
                prompt_tokens=estimate_messages_tokens(self.prompt_messages),
                completion_tokens=estimate_tokens(full_text),
                estimated=True,
            )

        _print_stream_footer(final_usage, elapsed)
        return full_text, final_usage


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
    renderer = NodeStreamRenderer(
        qualified_model=qualified_model,
        prompt_messages=prompt_messages,
    )
    renderer.start()
    tool_calls: list[ToolCall] = []
    try:
        async for chunk in chunks:
            if chunk.delta or chunk.usage is not None:
                renderer.feed(chunk.delta, usage=chunk.usage)
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
    except Exception:
        if renderer._live is not None:
            renderer._live.__exit__(None, None, None)
            renderer._live = None
        raise

    full_text, final_usage = renderer.finish(tool_names=[tc.name for tc in tool_calls])
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

"""
Chat message protocol and context window accounting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class MessageRole(StrEnum):
    """Supported roles in the chat message protocol."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class TokenUsage:
    """Token counts for a single completion turn."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated: bool = False

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class ChatMessage:
    """Single message in a conversation."""

    role: MessageRole
    content: str
    model: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    usage: TokenUsage | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_openai_dict(self) -> dict[str, Any]:
        """Serialize to OpenAI-compatible chat message payload."""
        payload: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            payload["name"] = self.name
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            payload["tool_calls"] = self.tool_calls
        return payload


def estimate_tokens(text: str) -> int:
    """Fast heuristic token estimate (~4 chars per token) when exact counts are absent."""
    if not text:
        return 0
    return max(1, len(text) // 4 + 1)


def estimate_messages_tokens(messages: list[ChatMessage]) -> int:
    """Estimate total prompt tokens for a list of messages."""
    return sum(estimate_tokens(m.content) + 4 for m in messages)


@dataclass
class ContextBudget:
    """Tracks current conversation context usage against the active model limit."""

    used_tokens: int
    context_window: int | None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    @property
    def remaining_tokens(self) -> int | None:
        if self.context_window is None:
            return None
        return max(0, self.context_window - self.used_tokens)

    @property
    def utilization_pct(self) -> float | None:
        if not self.context_window:
            return None
        return min(100.0, (self.used_tokens / self.context_window) * 100.0)

    def fits(self, target_window: int | None, reserve_output: int = 1024) -> bool:
        """Check whether current context fits within a target model's context window."""
        if target_window is None:
            return True
        return self.used_tokens + reserve_output <= target_window

    def format_summary(self) -> str:
        """Human-readable budget summary, showing 'unknown' when window limit is unknown."""
        if self.context_window is None:
            return f"~{self.used_tokens:,} tokens / unknown limit"
        pct = self.utilization_pct or 0.0
        return f"{self.used_tokens:,} / {self.context_window:,} tokens ({pct:.0f}%)"


"""
Chat message protocol, LangChain message conversions, and context window accounting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ToolCall as LCToolCall,
)


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

    def to_langchain_message(self) -> BaseMessage:
        """Convert this ChatMessage into a LangChain BaseMessage."""
        if self.role == MessageRole.SYSTEM:
            return SystemMessage(content=self.content)
        if self.role == MessageRole.TOOL:
            return ToolMessage(
                content=self.content,
                name=self.name or "tool",
                tool_call_id=self.tool_call_id or "call_0",
            )
        if self.role == MessageRole.ASSISTANT:
            lc_calls: list[LCToolCall] = []
            for tc in self.tool_calls or []:
                if "function" in tc and isinstance(tc["function"], dict):
                    fn = tc["function"]
                    raw_args = fn.get("arguments", "{}")
                    try:
                        parsed = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except json.JSONDecodeError:
                        parsed = {}
                    lc_calls.append(
                        LCToolCall(
                            id=str(tc.get("id") or "call_0"),
                            name=str(fn.get("name", "")),
                            args=parsed if isinstance(parsed, dict) else {},
                        )
                    )
                else:
                    args = tc.get("args", {})
                    lc_calls.append(
                        LCToolCall(
                            id=str(tc.get("id") or "call_0"),
                            name=str(tc.get("name", "")),
                            args=args if isinstance(args, dict) else {},
                        )
                    )
            return AIMessage(content=self.content, tool_calls=lc_calls)
        return HumanMessage(content=self.content)

    @classmethod
    def from_langchain_message(
        cls,
        message: BaseMessage,
        *,
        model: str | None = None,
    ) -> ChatMessage:
        """Construct a ChatMessage from a LangChain BaseMessage."""
        text = str(message.text) if hasattr(message, "text") else str(message.content)
        if isinstance(message, SystemMessage):
            return cls(role=MessageRole.SYSTEM, content=text)
        if isinstance(message, ToolMessage):
            return cls(
                role=MessageRole.TOOL,
                content=text,
                name=message.name,
                tool_call_id=message.tool_call_id,
            )
        if isinstance(message, AIMessage):
            serialized_calls: list[dict[str, Any]] | None = None
            if message.tool_calls:
                serialized_calls = [
                    {
                        "id": str(tc.get("id") or f"call_{idx}"),
                        "type": "function",
                        "function": {
                            "name": str(tc.get("name", "")),
                            "arguments": json.dumps(tc.get("args", {})),
                        },
                    }
                    for idx, tc in enumerate(message.tool_calls)
                ]
            usage: TokenUsage | None = None
            if message.usage_metadata:
                usage = TokenUsage(
                    prompt_tokens=int(message.usage_metadata.get("input_tokens", 0)),
                    completion_tokens=int(message.usage_metadata.get("output_tokens", 0)),
                    estimated=False,
                )
            return cls(
                role=MessageRole.ASSISTANT,
                content=text,
                model=model,
                tool_calls=serialized_calls,
                usage=usage,
            )
        return cls(role=MessageRole.USER, content=text)


def to_langchain_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    """Convert ChatMessage history into LangChain messages, coalescing system blocks."""
    system_blocks: list[str] = []
    other_msgs: list[BaseMessage] = []
    for msg in messages:
        if msg.role == MessageRole.SYSTEM:
            if msg.content.strip():
                system_blocks.append(msg.content)
        else:
            other_msgs.append(msg.to_langchain_message())
    if system_blocks:
        return [SystemMessage(content="\n\n".join(system_blocks)), *other_msgs]
    return other_msgs


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

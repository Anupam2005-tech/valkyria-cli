"""
LangChain chat model factory and streaming adapter for Groq, Gemini, and NVIDIA NIM.
"""

from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from pydantic import SecretStr

from valkyria.chat.messages import ChatMessage, TokenUsage, to_langchain_messages

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.runnables import Runnable
    from langchain_core.tools import BaseTool

_SUGGESTED_MODEL_RE = re.compile(r"models/([A-Za-z0-9_.\-]+)")
_STATUS_CODE_RE = re.compile(r"\b(400|401|403|404|408|409|422|429|500|502|503|504)\b")


class ChatStreamError(RuntimeError):
    """Raised when a provider rejects or fails during a streaming completion."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        suggested_model: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.suggested_model = suggested_model


@dataclass
class ToolCall:
    """Normalized tool/function invocation emitted by any provider."""

    id: str
    name: str
    arguments: dict[str, Any]

    def to_openai_dict(self) -> dict[str, Any]:
        """Serialize back into an OpenAI assistant tool_calls entry."""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments),
            },
        }


@dataclass
class StreamChunk:
    """A single streamed event from a LangChain model."""

    delta: str = ""
    usage: TokenUsage | None = None
    finish_reason: str | None = None
    tool_calls: list[ToolCall] | None = None


def build_chat_model(
    *,
    provider_key: str,
    model_id: str,
    api_key: str,
    temperature: float = 0.7,
    streaming: bool = True,
) -> BaseChatModel:
    """Instantiate the official LangChain chat model for Groq, Gemini, or NVIDIA NIM."""
    pkey = provider_key.lower()
    secret = SecretStr(api_key)
    if pkey == "groq":
        return ChatGroq(
            model=model_id,
            api_key=secret,
            temperature=temperature,
            streaming=streaming,
        )
    if pkey == "gemini":
        return ChatGoogleGenerativeAI(
            model=model_id,
            api_key=secret,
            temperature=temperature,
            streaming=streaming,
        )
    if pkey == "nvidia":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return ChatNVIDIA(
                model=model_id,
                api_key=api_key,
                temperature=temperature,
            )
    raise ChatStreamError(f"Unsupported chat provider: {provider_key}")


def bind_model_tools(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
) -> Runnable[Any, BaseMessage]:
    """Bind LangChain tools onto a BaseChatModel while quieting NIM catalog warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return model.bind_tools(list(tools))


def parse_langchain_error(
    exc: Exception,
    *,
    provider_key: str,
    model_id: str,
) -> ChatStreamError:
    """Normalize LangChain / provider SDK exceptions into ChatStreamError."""
    if isinstance(exc, ChatStreamError):
        return exc

    status_code: int | None = None
    for attr in ("status_code", "code"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            status_code = val
            break
    if status_code is None:
        response = getattr(exc, "response", None)
        resp_code = getattr(response, "status_code", None)
        if isinstance(resp_code, int):
            status_code = resp_code

    raw_msg = str(exc).strip()
    if status_code is None:
        m = _STATUS_CODE_RE.search(raw_msg)
        if m:
            status_code = int(m.group(1))

    clean_msg = raw_msg or type(exc).__name__
    if len(clean_msg) > 400:
        clean_msg = clean_msg[:397] + "..."

    suggested_model: str | None = None
    if provider_key.lower() == "gemini":
        for match in _SUGGESTED_MODEL_RE.findall(clean_msg):
            if match != model_id:
                suggested_model = f"gemini/{match}"
                break

    prefix = f"HTTP {status_code}: " if status_code is not None else ""
    return ChatStreamError(
        f"{prefix}{clean_msg}",
        status_code=status_code,
        suggested_model=suggested_model,
    )


def _extract_tool_calls(chunk: AIMessageChunk) -> list[ToolCall]:
    """Extract normalized ToolCall objects from an accumulated AIMessageChunk."""
    calls: list[ToolCall] = []
    for idx, tc in enumerate(chunk.tool_calls or []):
        name = str(tc.get("name", ""))
        if not name:
            continue
        args = tc.get("args")
        calls.append(
            ToolCall(
                id=str(tc.get("id") or f"call_{idx}"),
                name=name,
                arguments=dict(args) if isinstance(args, dict) else {},
            )
        )
    return calls


async def stream_chat_completion(
    *,
    provider_key: str,
    model_id: str,
    api_key: str,
    messages: list[ChatMessage],
    temperature: float = 0.7,
    tools: Sequence[BaseTool] | None = None,
) -> AsyncIterator[StreamChunk]:
    """Stream completions through LangChain's BaseChatModel.astream API."""
    model = build_chat_model(
        provider_key=provider_key,
        model_id=model_id,
        api_key=api_key,
        temperature=temperature,
        streaming=True,
    )
    runnable: Runnable[Any, BaseMessage] = bind_model_tools(model, tools) if tools else model
    lc_messages = to_langchain_messages(messages)

    accumulated: AIMessageChunk | None = None
    try:
        async for item in runnable.astream(lc_messages):
            if isinstance(item, AIMessageChunk):
                accumulated = item if accumulated is None else accumulated + item
                delta = str(item.text)
                usage: TokenUsage | None = None
                if item.usage_metadata:
                    usage = TokenUsage(
                        prompt_tokens=int(item.usage_metadata.get("input_tokens", 0)),
                        completion_tokens=int(item.usage_metadata.get("output_tokens", 0)),
                        estimated=False,
                    )
                finish_reason = item.response_metadata.get("finish_reason")
                if delta or usage is not None or finish_reason:
                    yield StreamChunk(
                        delta=delta,
                        usage=usage,
                        finish_reason=str(finish_reason) if finish_reason else None,
                    )
            elif isinstance(item, BaseMessage):
                msg_delta = str(item.text) if hasattr(item, "text") else str(item.content)
                if msg_delta:
                    yield StreamChunk(delta=msg_delta)

        if accumulated is not None:
            tool_calls = _extract_tool_calls(accumulated)
            if tool_calls:
                yield StreamChunk(tool_calls=tool_calls)
    except Exception as exc:
        raise parse_langchain_error(
            exc,
            provider_key=provider_key,
            model_id=model_id,
        ) from exc

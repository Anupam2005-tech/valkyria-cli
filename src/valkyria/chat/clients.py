"""
Streaming chat completion clients for Groq, Gemini, and NVIDIA NIM, with tool calling.

Groq and NVIDIA NIM share the OpenAI SSE streaming protocol via a single helper;
Gemini uses its streamGenerateContent?alt=sse endpoint with functionDeclarations.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

from valkyrie.chat.messages import ChatMessage, MessageRole, TokenUsage
from valkyrie.providers.gemini import GEMINI_API_BASE
from valkyrie.providers.groq import GROQ_API_BASE
from valkyrie.providers.nvidia import NVIDIA_API_BASE

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_SUGGESTED_MODEL_RE = re.compile(r"models/([A-Za-z0-9_.\-]+)")


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
    """A single streamed event from a provider."""

    delta: str = ""
    usage: TokenUsage | None = None
    finish_reason: str | None = None
    tool_calls: list[ToolCall] | None = None


def _parse_provider_error(
    *,
    provider_key: str,
    model_id: str,
    status_code: int,
    raw_body: str,
) -> ChatStreamError:
    """Extract clean message and optional replacement suggestion from provider error JSON."""
    clean_msg = raw_body.strip()
    try:
        parsed = json.loads(raw_body)
        if isinstance(parsed, dict):
            err_obj = parsed.get("error")
            if isinstance(err_obj, dict) and err_obj.get("message"):
                clean_msg = str(err_obj["message"])
            elif parsed.get("message"):
                clean_msg = str(parsed["message"])
    except json.JSONDecodeError:
        pass

    if len(clean_msg) > 400:
        clean_msg = clean_msg[:397] + "..."

    suggested_model: str | None = None
    if provider_key == "gemini":
        for match in _SUGGESTED_MODEL_RE.findall(clean_msg):
            if match != model_id:
                suggested_model = f"gemini/{match}"
                break

    return ChatStreamError(
        f"HTTP {status_code}: {clean_msg}",
        status_code=status_code,
        suggested_model=suggested_model,
    )


def _finalize_openai_tool_calls(acc: dict[int, dict[str, Any]]) -> list[ToolCall]:
    """Convert accumulated OpenAI streaming delta tool_calls into ToolCall objects."""
    calls: list[ToolCall] = []
    for idx in sorted(acc.keys()):
        entry = acc[idx]
        raw_args = "".join(entry["args_parts"]).strip()
        try:
            parsed = json.loads(raw_args) if raw_args else {}
            args = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            args = {"raw_arguments": raw_args}
        calls.append(
            ToolCall(
                id=entry["id"] or f"call_{idx}",
                name=entry["name"],
                arguments=args,
            )
        )
    return calls


async def _stream_openai_compatible(
    *,
    provider_key: str,
    base_url: str,
    api_key: str,
    model_id: str,
    messages: list[ChatMessage],
    temperature: float = 0.7,
    include_stream_usage: bool = True,
    tools: list[dict[str, Any]] | None = None,
) -> AsyncIterator[StreamChunk]:
    """Stream completions from any OpenAI-compatible SSE endpoint."""
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": [m.to_openai_dict() for m in messages],
        "stream": True,
        "temperature": temperature,
    }
    if include_stream_usage:
        payload["stream_options"] = {"include_usage": True}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    tool_acc: dict[int, dict[str, Any]] = {}

    try:
        async with (
            httpx.AsyncClient(timeout=60.0) as client,
            client.stream(
                "POST",
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp,
        ):
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", errors="replace")
                raise _parse_provider_error(
                    provider_key=provider_key,
                    model_id=model_id,
                    status_code=resp.status_code,
                    raw_body=body,
                )

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                usage_obj = event.get("usage")
                usage: TokenUsage | None = None
                if isinstance(usage_obj, dict):
                    usage = TokenUsage(
                        prompt_tokens=int(usage_obj.get("prompt_tokens", 0)),
                        completion_tokens=int(usage_obj.get("completion_tokens", 0)),
                        estimated=False,
                    )

                choices = event.get("choices") or []
                if not choices:
                    if usage is not None:
                        yield StreamChunk(usage=usage)
                    continue

                choice = choices[0]
                delta_obj = choice.get("delta", {})
                delta = delta_obj.get("content") or ""
                finish_reason = choice.get("finish_reason")

                for tc in delta_obj.get("tool_calls") or []:
                    idx = int(tc.get("index", 0))
                    slot = tool_acc.setdefault(
                        idx,
                        {"id": "", "name": "", "args_parts": []},
                    )
                    if tc.get("id"):
                        slot["id"] = str(tc["id"])
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        slot["name"] += str(fn["name"])
                    if fn.get("arguments"):
                        slot["args_parts"].append(str(fn["arguments"]))

                if delta or usage is not None or finish_reason:
                    yield StreamChunk(delta=delta, usage=usage, finish_reason=finish_reason)

        if tool_acc:
            yield StreamChunk(tool_calls=_finalize_openai_tool_calls(tool_acc))
    except httpx.HTTPError as exc:
        raise ChatStreamError(f"Network error: {exc}") from exc


def _build_gemini_contents(messages: list[ChatMessage]) -> tuple[list[str], list[dict[str, Any]]]:
    """Convert ChatMessage history into Gemini systemInstruction parts and contents."""
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []

    for msg in messages:
        if msg.role == MessageRole.SYSTEM:
            system_parts.append(msg.content)
            continue

        if msg.role == MessageRole.ASSISTANT:
            parts: list[dict[str, Any]] = []
            if msg.content:
                parts.append({"text": msg.content})
            for tc in msg.tool_calls or []:
                fn = tc.get("function", {})
                raw_args = fn.get("arguments", "{}")
                try:
                    parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    parsed_args = {}
                parts.append(
                    {
                        "functionCall": {
                            "name": fn.get("name", ""),
                            "args": parsed_args if isinstance(parsed_args, dict) else {},
                        }
                    }
                )
            if parts:
                contents.append({"role": "model", "parts": parts})
            continue

        if msg.role == MessageRole.TOOL:
            resp_part = {
                "functionResponse": {
                    "name": msg.name or "tool",
                    "response": {"result": msg.content},
                }
            }
            if contents and contents[-1]["role"] == "user" and any(
                "functionResponse" in p for p in contents[-1]["parts"]
            ):
                contents[-1]["parts"].append(resp_part)
            else:
                contents.append({"role": "user", "parts": [resp_part]})
            continue

        contents.append({"role": "user", "parts": [{"text": msg.content}]})

    return system_parts, contents


async def _stream_gemini(
    *,
    api_key: str,
    model_id: str,
    messages: list[ChatMessage],
    temperature: float = 0.7,
    function_declarations: list[dict[str, Any]] | None = None,
) -> AsyncIterator[StreamChunk]:
    """Stream completions from Gemini streamGenerateContent?alt=sse."""
    system_parts, contents = _build_gemini_contents(messages)

    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": temperature},
    }
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
    if function_declarations:
        payload["tools"] = [{"functionDeclarations": function_declarations}]

    url = f"{GEMINI_API_BASE}/models/{model_id}:streamGenerateContent"
    params = {"alt": "sse", "key": api_key}

    call_seq = 0
    try:
        async with (
            httpx.AsyncClient(timeout=60.0) as client,
            client.stream("POST", url, params=params, json=payload) as resp,
        ):
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", errors="replace")
                raise _parse_provider_error(
                    provider_key="gemini",
                    model_id=model_id,
                    status_code=resp.status_code,
                    raw_body=body,
                )

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    continue

                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                usage: TokenUsage | None = None
                meta = event.get("usageMetadata")
                if isinstance(meta, dict):
                    usage = TokenUsage(
                        prompt_tokens=int(meta.get("promptTokenCount", 0)),
                        completion_tokens=int(meta.get("candidatesTokenCount", 0)),
                        estimated=False,
                    )

                candidates = event.get("candidates") or []
                text_parts: list[str] = []
                tool_calls: list[ToolCall] = []
                finish_reason: str | None = None
                if candidates:
                    cand = candidates[0]
                    finish_reason = cand.get("finishReason")
                    parts = cand.get("content", {}).get("parts", [])
                    for p in parts:
                        if not isinstance(p, dict):
                            continue
                        if "text" in p and p["text"]:
                            text_parts.append(str(p["text"]))
                        if "functionCall" in p and isinstance(p["functionCall"], dict):
                            fc = p["functionCall"]
                            call_seq += 1
                            args = fc.get("args")
                            tool_calls.append(
                                ToolCall(
                                    id=f"gemini_call_{call_seq}",
                                    name=str(fc.get("name", "")),
                                    arguments=args if isinstance(args, dict) else {},
                                )
                            )

                text_delta = "".join(text_parts)
                if text_delta or tool_calls or usage is not None or finish_reason:
                    yield StreamChunk(
                        delta=text_delta,
                        usage=usage,
                        finish_reason=finish_reason,
                        tool_calls=tool_calls or None,
                    )
    except httpx.HTTPError as exc:
        raise ChatStreamError(f"Network error: {exc}") from exc


async def stream_chat_completion(
    *,
    provider_key: str,
    model_id: str,
    api_key: str,
    messages: list[ChatMessage],
    temperature: float = 0.7,
    openai_tools: list[dict[str, Any]] | None = None,
    gemini_declarations: list[dict[str, Any]] | None = None,
) -> AsyncIterator[StreamChunk]:
    """Dispatch streaming completion to the requested provider."""
    pkey = provider_key.lower()
    if pkey == "groq":
        async for chunk in _stream_openai_compatible(
            provider_key="groq",
            base_url=GROQ_API_BASE,
            api_key=api_key,
            model_id=model_id,
            messages=messages,
            temperature=temperature,
            include_stream_usage=True,
            tools=openai_tools,
        ):
            yield chunk
    elif pkey == "nvidia":
        async for chunk in _stream_openai_compatible(
            provider_key="nvidia",
            base_url=NVIDIA_API_BASE,
            api_key=api_key,
            model_id=model_id,
            messages=messages,
            temperature=temperature,
            include_stream_usage=False,
            tools=openai_tools,
        ):
            yield chunk
    elif pkey == "gemini":
        async for chunk in _stream_gemini(
            api_key=api_key,
            model_id=model_id,
            messages=messages,
            temperature=temperature,
            function_declarations=gemini_declarations,
        ):
            yield chunk
    else:
        raise ChatStreamError(f"Unsupported chat provider: {provider_key}")

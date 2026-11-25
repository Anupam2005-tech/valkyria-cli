"""Tests for Phase 6 chat engine, streaming clients, context budget, and CLI."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from valkyrie.chat.clients import ChatStreamError, StreamChunk, stream_chat_completion
from valkyrie.chat.engine import ChatEngine, _handle_slash_command
from valkyrie.chat.messages import ChatMessage, ContextBudget, MessageRole
from valkyrie.cli.main import cli
from valkyrie.core.config import UserProfile, ValkyrieConfig
from valkyrie.providers.base import ModelCapability, ModelInfo
from valkyrie.providers.registry import ModelRegistry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _FakeStreamResponse:
    """Minimal async context-manager mocking httpx.Response for SSE streaming."""

    def __init__(self, lines: list[str], status_code: int = 200, error_body: bytes = b"") -> None:
        self._lines = lines
        self.status_code = status_code
        self._error_body = error_body

    async def __aenter__(self) -> _FakeStreamResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def aread(self) -> bytes:
        return self._error_body

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line


def _make_fake_client(
    lines: list[str],
    status_code: int = 200,
    error_body: bytes = b"",
) -> MagicMock:
    client = MagicMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    client.stream.return_value = _FakeStreamResponse(
        lines, status_code=status_code, error_body=error_body
    )
    return client


class TestContextBudget:
    """Tests for token accounting and window budget checks."""

    def test_budget_known_and_unknown_windows(self) -> None:
        b1 = ContextBudget(used_tokens=2000, context_window=8192)
        assert b1.remaining_tokens == 6192
        assert b1.fits(8192) is True
        assert b1.fits(2500, reserve_output=1024) is False
        assert "2,000 / 8,192" in b1.format_summary()

        b_unknown = ContextBudget(used_tokens=500, context_window=None)
        assert b_unknown.remaining_tokens is None
        assert b_unknown.fits(None) is True
        assert "unknown limit" in b_unknown.format_summary()


class TestStreamingClients:
    """Tests for Groq, NVIDIA, and Gemini SSE streaming clients."""

    def test_groq_sse_streaming_with_usage(self) -> None:
        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"content":" world"},"finish_reason":"stop"}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":4}}',
            "data: [DONE]",
        ]
        fake_client = _make_fake_client(sse_lines)

        async def _collect() -> list[StreamChunk]:
            with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
                return [
                    c
                    async for c in stream_chat_completion(
                        provider_key="groq",
                        model_id="llama-3.3-70b-versatile",
                        api_key="gsk_test",
                        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
                    )
                ]

        chunks = asyncio.run(_collect())
        assert "".join(c.delta for c in chunks) == "Hello world"
        usages = [c.usage for c in chunks if c.usage is not None]
        assert len(usages) == 1
        assert usages[0].prompt_tokens == 12
        assert usages[0].completion_tokens == 4

    def test_gemini_sse_streaming(self) -> None:
        sse_lines = [
            'data: {"candidates":[{"content":{"parts":[{"text":"Hi there"}]}}]}',
            (
                'data: {"candidates":[{"content":{"parts":[{"text":"!"}]},'
                '"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":8,"candidatesTokenCount":3}}'
            ),
        ]
        fake_client = _make_fake_client(sse_lines)

        async def _collect() -> list[StreamChunk]:
            with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
                return [
                    c
                    async for c in stream_chat_completion(
                        provider_key="gemini",
                        model_id="gemini-2.0-flash",
                        api_key="AIza_test",
                        messages=[
                            ChatMessage(role=MessageRole.SYSTEM, content="Be brief."),
                            ChatMessage(role=MessageRole.USER, content="hi"),
                        ],
                    )
                ]

        chunks = asyncio.run(_collect())
        assert "".join(c.delta for c in chunks) == "Hi there!"
        usages = [c.usage for c in chunks if c.usage is not None]
        assert usages[-1].prompt_tokens == 8
        assert usages[-1].completion_tokens == 3

    def test_http_error_raises_chat_stream_error(self) -> None:
        fake_client = _make_fake_client([], status_code=401, error_body=b"Invalid API key")

        async def _run() -> None:
            with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
                async for _ in stream_chat_completion(
                    provider_key="nvidia",
                    model_id="meta/llama-3.1-70b-instruct",
                    api_key="bad",
                    messages=[ChatMessage(role=MessageRole.USER, content="hi")],
                ):
                    pass

        try:
            asyncio.run(_run())
            raise AssertionError("Expected ChatStreamError")
        except ChatStreamError as exc:
            assert "401" in str(exc)


class TestChatEngine:
    """Tests for ChatEngine turn execution and /model switching."""

    def _build_engine(self) -> ChatEngine:
        m_small = ModelInfo(
            id="small-model",
            name="Small",
            provider="groq",
            capabilities=[ModelCapability.CHAT],
            context_window=200,
        )
        m_large = ModelInfo(
            id="gemini-2.0-flash",
            name="Gemini 2.0 Flash",
            provider="gemini",
            capabilities=[ModelCapability.CHAT],
            context_window=1_000_000,
        )
        m_retired = ModelInfo(
            id="old-model",
            name="Old",
            provider="groq",
            capabilities=[ModelCapability.CHAT],
            context_window=4096,
            is_active=False,
        )
        reg = ModelRegistry(
            models={
                m_small.qualified_id: m_small,
                m_large.qualified_id: m_large,
                m_retired.qualified_id: m_retired,
            }
        )
        cfg = ValkyrieConfig(profile=UserProfile(name="Anupam"))
        return ChatEngine(
            config=cfg,
            registry=reg,
            api_keys={"groq": "gsk_x", "gemini": "AIza_x"},
            initial_model="gemini/gemini-2.0-flash",
        )

    def test_send_turn_updates_history_and_tokens(self) -> None:
        engine = self._build_engine()
        sse_lines = [
            'data: {"candidates":[{"content":{"parts":[{"text":"Pong"}]},"finishReason":"STOP"}],'
            '"usageMetadata":{"promptTokenCount":15,"candidatesTokenCount":2}}'
        ]
        fake_client = _make_fake_client(sse_lines)

        with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
            reply = asyncio.run(engine.send_turn("Ping"))

        assert reply == "Pong"
        assert len(engine.messages) == 3
        assert engine.messages[-1].role == MessageRole.ASSISTANT
        assert engine.total_prompt_tokens == 15
        assert engine.total_completion_tokens == 2

    def test_switch_model_checks_budget_and_validity(self) -> None:
        engine = self._build_engine()
        # Add enough text to exceed small-model's 200-token window
        engine.messages.append(ChatMessage(role=MessageRole.USER, content="word " * 300))

        ok, msg = engine.switch_model("groq/small-model")
        assert ok is False
        assert "exceeds" in msg

        # Force truncate clears history and switches
        ok_force, _ = engine.switch_model("groq/small-model", force_truncate=True)
        assert ok_force is True
        assert engine.active_model == "groq/small-model"
        assert len(engine.messages) == 1

        # Inactive/retired model rejected
        ok_ret, msg_ret = engine.switch_model("groq/old-model")
        assert ok_ret is False
        assert "inactive" in msg_ret

        # Slash command exit & provider filtering / shorthand /model switch
        assert _handle_slash_command("/exit", engine) is False
        assert _handle_slash_command("/budget", engine) is True
        assert _handle_slash_command("/model groq", engine) is True
        assert _handle_slash_command("/model gemini-2.0-flash", engine) is True
        assert engine.active_model == "gemini/gemini-2.0-flash"

    def test_slash_new_resets_ephemeral_context_window(self) -> None:
        engine = self._build_engine()
        engine.messages.append(ChatMessage(role=MessageRole.USER, content="Old context"))
        engine.messages.append(ChatMessage(role=MessageRole.ASSISTANT, content="Old reply"))
        engine.total_prompt_tokens = 250
        engine.total_completion_tokens = 80
        engine.last_suggested_model = "groq/small-model"

        assert _handle_slash_command("/new", engine) is True
        assert engine.session_id is None
        assert len(engine.messages) == 1
        assert engine.messages[0].role == MessageRole.SYSTEM
        assert engine.total_prompt_tokens == 0
        assert engine.total_completion_tokens == 0
        assert engine.last_suggested_model is None

    def test_deprecated_404_error_extracts_replacement_suggestion(self) -> None:
        m_old = ModelInfo(
            id="gemini-2.5-flash",
            name="Gemini 2.5 Flash",
            provider="gemini",
            capabilities=[ModelCapability.CHAT],
            context_window=1_000_000,
        )
        m_new = ModelInfo(
            id="gemini-3.8-flash",
            name="Gemini 3.8 Flash",
            provider="gemini",
            capabilities=[ModelCapability.CHAT],
            context_window=1_000_000,
        )
        reg = ModelRegistry(models={m_old.qualified_id: m_old, m_new.qualified_id: m_new})
        engine = ChatEngine(
            config=ValkyrieConfig(),
            registry=reg,
            api_keys={"gemini": "AIza_x"},
            initial_model="gemini/gemini-2.5-flash",
        )
        err_json = (
            b'{"error":{"code":404,"message":"This model models/gemini-2.5-flash '
            b"is no longer available to new users. Please update your code to use "
            b'models/gemini-3.8-flash for the latest features."}}'
        )
        fake_client = _make_fake_client([], status_code=404, error_body=err_json)

        with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
            reply = asyncio.run(engine.send_turn("hello"))

        assert reply is None
        assert len(engine.messages) == 1
        assert m_old.is_active is False
        assert engine.last_suggested_model == "gemini/gemini-3.8-flash"


class TestChatCli:
    """Tests for valkyrie chat CLI command."""

    def test_chat_requires_configured_model(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.json"
        with patch("valkyrie.core.config.get_config_path", return_value=cfg_file):
            runner = CliRunner()
            res = runner.invoke(cli, ["chat"])
            assert res.exit_code == 1
            assert "No chat model configured" in res.output

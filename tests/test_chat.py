"""Tests for LangChain chat clients, LangGraph multi-node /plan workflow, budget, and CLI."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from click.testing import CliRunner
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from pydantic import Field

from valkyria.chat.clients import (
    ChatStreamError,
    StreamChunk,
    build_chat_model,
    stream_chat_completion,
)
from valkyria.chat.engine import ChatEngine, _handle_slash_command
from valkyria.chat.messages import ChatMessage, ContextBudget, MessageRole
from valkyria.cli.main import cli
from valkyria.core.config import UserProfile, ValkyriaConfig
from valkyria.providers.base import ModelCapability, ModelInfo
from valkyria.providers.registry import ModelRegistry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _ProviderApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class _FakeLangChainChatModel(BaseChatModel):
    """Test LangChain BaseChatModel supporting streaming chunks, tool calls, and errors."""

    scripted: list[list[AIMessageChunk] | Exception] = Field(default_factory=list)
    recorded_inputs: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "fake-valkyria"

    def bind_tools(self, tools: Any, **kwargs: Any) -> _FakeLangChainChatModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.recorded_inputs.append(list(messages))
        item = self.scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        merged = item[0]
        for nxt in item[1:]:
            merged = merged + nxt
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content=merged.content,
                        tool_calls=merged.tool_calls,
                        usage_metadata=merged.usage_metadata,
                    )
                )
            ]
        )

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.recorded_inputs.append(list(messages))
        item = self.scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        for chunk in item:
            if run_manager and chunk.text:
                await run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            yield ChatGenerationChunk(message=chunk)


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


class TestLangChainClients:
    """Tests for official LangChain chat model factory and streaming adapter."""

    def test_build_chat_model_uses_official_langchain_integrations(self) -> None:
        groq_m = build_chat_model(
            provider_key="groq",
            model_id="llama-3.3-70b-versatile",
            api_key="gsk_test",
        )
        gem_m = build_chat_model(
            provider_key="gemini",
            model_id="gemini-2.5-flash",
            api_key="AIza_test",
        )
        nv_m = build_chat_model(
            provider_key="nvidia",
            model_id="meta/llama-3.1-70b-instruct",
            api_key="nvapi-test",
        )
        assert isinstance(groq_m, ChatGroq)
        assert isinstance(gem_m, ChatGoogleGenerativeAI)
        assert isinstance(nv_m, ChatNVIDIA)

        try:
            build_chat_model(provider_key="unknown", model_id="x", api_key="k")
            raise AssertionError("Expected ChatStreamError")
        except ChatStreamError as exc:
            assert "Unsupported chat provider" in str(exc)

    def test_groq_streaming_with_usage(self) -> None:
        fake_model = _FakeLangChainChatModel(
            scripted=[
                [
                    AIMessageChunk(content="Hello"),
                    AIMessageChunk(
                        content=" world",
                        usage_metadata={"input_tokens": 12, "output_tokens": 4, "total_tokens": 16},
                        response_metadata={"finish_reason": "stop"},
                    ),
                ]
            ]
        )

        async def _collect() -> list[StreamChunk]:
            with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
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

    def test_gemini_streaming_coalesces_system_messages(self) -> None:
        fake_model = _FakeLangChainChatModel(
            scripted=[
                [
                    AIMessageChunk(content="Hi there"),
                    AIMessageChunk(
                        content="!",
                        usage_metadata={"input_tokens": 8, "output_tokens": 3, "total_tokens": 11},
                    ),
                ]
            ]
        )

        async def _collect() -> list[StreamChunk]:
            with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
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
        fake_model = _FakeLangChainChatModel(
            scripted=[_ProviderApiError("Invalid API key", status_code=401)]
        )

        async def _run() -> None:
            with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
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
            assert exc.status_code == 401
            assert "401" in str(exc)


class TestChatEngineAndLangGraph:
    """Tests for ChatEngine LangGraph execution, /plan workflow, and /model switching."""

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
        cfg = ValkyriaConfig(profile=UserProfile(name="Anupam"))
        return ChatEngine(
            config=cfg,
            registry=reg,
            api_keys={"groq": "gsk_x", "gemini": "AIza_x"},
            initial_model="gemini/gemini-2.0-flash",
        )

    def test_send_turn_updates_history_and_tokens(self) -> None:
        engine = self._build_engine()
        fake_model = _FakeLangChainChatModel(
            scripted=[
                [
                    AIMessageChunk(
                        content="Pong",
                        usage_metadata={"input_tokens": 15, "output_tokens": 2, "total_tokens": 17},
                    )
                ]
            ]
        )

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(engine.send_turn("Ping"))

        assert reply == "Pong"
        assert len(engine.messages) == 3
        assert engine.messages[-1].role == MessageRole.ASSISTANT
        assert engine.total_prompt_tokens == 15
        assert engine.total_completion_tokens == 2

    def test_switch_model_checks_budget_and_validity(self) -> None:
        engine = self._build_engine()
        engine.messages.append(ChatMessage(role=MessageRole.USER, content="word " * 300))

        ok, msg = engine.switch_model("groq/small-model")
        assert ok is False
        assert "exceeds" in msg

        ok_force, _ = engine.switch_model("groq/small-model", force_truncate=True)
        assert ok_force is True
        assert engine.active_model == "groq/small-model"
        assert len(engine.messages) == 1

        ok_ret, msg_ret = engine.switch_model("groq/old-model")
        assert ok_ret is False
        assert "inactive" in msg_ret

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
            config=ValkyriaConfig(),
            registry=reg,
            api_keys={"gemini": "AIza_x"},
            initial_model="gemini/gemini-2.5-flash",
        )
        err = _ProviderApiError(
            "This model models/gemini-2.5-flash is no longer available to new users. "
            "Please update your code to use models/gemini-3.8-flash for the latest features.",
            status_code=404,
        )
        fake_model = _FakeLangChainChatModel(scripted=[err])

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(engine.send_turn("hello"))

        assert reply is None
        assert len(engine.messages) == 1
        assert m_old.is_active is False
        assert engine.last_suggested_model == "gemini/gemini-3.8-flash"

    def test_plan_graph_planner_safety_gate_edit_approve_executor_evaluator(
        self, tmp_path: Path
    ) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_x"},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=ws,
            auto_approve_tools=False,
        )

        # 1. Planner emits initial plan -> plan_safety_gate interrupts -> user asks to edit
        # 2. Planner emits revised plan -> plan_safety_gate interrupts -> user approves
        # 3. Executor invokes write_file -> tool_safety_gate interrupts -> user approves
        # 4. Executor emits summary -> Evaluator returns PASS
        fake_model = _FakeLangChainChatModel(
            scripted=[
                [AIMessageChunk(content="Plan v1:\n1. Create notes.md")],
                [AIMessageChunk(content="Plan v2:\n1. Create notes.md with header")],
                [
                    AIMessageChunk(
                        content="",
                        tool_calls=[
                            {
                                "id": "call_w1",
                                "name": "write_file",
                                "args": {"path": "notes.md", "content": "# Plan Notes\n"},
                            }
                        ],
                    )
                ],
                [AIMessageChunk(content="Created notes.md with header.")],
                [AIMessageChunk(content="PASS: notes.md created as planned.")],
            ]
        )

        plan_decisions = [
            {"action": "edit", "feedback": "Add a header"},
            {"action": "approve"},
        ]

        with (
            patch("valkyria.chat.clients.build_chat_model", return_value=fake_model),
            patch.object(engine, "_prompt_plan_approval", side_effect=plan_decisions),
            patch.object(
                engine,
                "_prompt_tool_batch_approval",
                return_value={"approved_ids": ["call_w1"], "denied_ids": []},
            ),
        ):
            reply = asyncio.run(engine.run_plan("Create notes.md"))

        assert reply == "Created notes.md with header."
        assert (ws / "notes.md").read_text() == "# Plan Notes\n"

    def test_plan_graph_deny_cancels_before_execution(self, tmp_path: Path) -> None:
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_x"},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=tmp_path,
            auto_approve_tools=False,
        )
        fake_model = _FakeLangChainChatModel(
            scripted=[[AIMessageChunk(content="Plan:\n1. Delete everything")]]
        )

        with (
            patch("valkyria.chat.clients.build_chat_model", return_value=fake_model),
            patch.object(engine, "_prompt_plan_approval", return_value={"action": "deny"}),
        ):
            reply = asyncio.run(engine.run_plan("Delete files"))

        assert reply == "Plan cancelled by user."
        assert len(fake_model.recorded_inputs) == 1

    def test_plan_graph_evaluator_retry_loop(self, tmp_path: Path) -> None:
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_x"},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=tmp_path,
            auto_approve_tools=True,
        )
        fake_model = _FakeLangChainChatModel(
            scripted=[
                [AIMessageChunk(content="Plan:\n1. Answer clearly")],
                [AIMessageChunk(content="Draft answer")],
                [AIMessageChunk(content="RETRY: Include exact conclusion.")],
                [AIMessageChunk(content="Final complete answer.")],
                [AIMessageChunk(content="PASS: Conclusion included.")],
            ]
        )

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(engine.run_plan("Provide conclusion"))

        assert reply == "Final complete answer."
        assert len(fake_model.recorded_inputs) == 5


class TestChatCli:
    """Tests for valkyria chat CLI command."""

    def test_chat_requires_configured_model(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.json"
        with patch("valkyria.core.config.get_config_path", return_value=cfg_file):
            runner = CliRunner()
            res = runner.invoke(cli, ["chat"])
            assert res.exit_code == 1
            assert "No chat model configured" in res.output

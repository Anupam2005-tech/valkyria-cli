"""Tests for JSON session persistence, LangGraph checkpoints, ChatEngine sync, and CLI."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TypedDict
from unittest.mock import patch

from click.testing import CliRunner
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import Field

from valkyria.chat.engine import ChatEngine, _handle_slash_command
from valkyria.chat.messages import ChatMessage, MessageRole, TokenUsage
from valkyria.cli.main import cli
from valkyria.core.config import ValkyriaConfig
from valkyria.providers.registry import ModelRegistry
from valkyria.sessions.checkpointer import JsonFileSaver
from valkyria.sessions.store import SessionStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _FakeLangChainModel(BaseChatModel):
    responses: list[AIMessage] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "fake-sessions"

    def bind_tools(self, tools: Any, **kwargs: Any) -> _FakeLangChainModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        msg = self.responses.pop(0)
        return ChatResult(generations=[ChatGeneration(message=msg)])

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        msg = self.responses.pop(0)
        text = msg.text if hasattr(msg, "text") else str(msg.content)
        chunk = AIMessageChunk(
            content=text,
            usage_metadata=msg.usage_metadata,
        )
        if run_manager and text:
            await run_manager.on_llm_new_token(text, chunk=chunk)
        yield ChatGenerationChunk(message=chunk)


class TestSessionStore:
    """Tests for JSON-backed SessionStore and JsonFileSaver operations (zero SQLite)."""

    def test_create_append_resume_and_prefix(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        store = SessionStore(sessions_dir=sessions_dir)
        sys_msg = ChatMessage(role=MessageRole.SYSTEM, content="System prompt")
        sess = store.create_session(
            active_model="groq/llama-3.3-70b-versatile",
            workspace_root="/tmp/ws",
            initial_messages=[sys_msg],
        )

        store.append_message(sess.id, ChatMessage(role=MessageRole.USER, content="How do I build?"))
        store.append_message(
            sess.id,
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content="Run uv build.",
                model="groq/llama-3.3-70b-versatile",
                usage=TokenUsage(prompt_tokens=20, completion_tokens=10),
            ),
        )
        store.auto_title_if_default(sess.id, "How do I build?")

        loaded = store.get_session(sess.id[:8])
        assert loaded is not None
        assert loaded.id == sess.id
        assert loaded.title == "How do I build?"
        assert loaded.message_count == 2
        assert loaded.total_prompt_tokens == 20
        assert loaded.total_completion_tokens == 10

        latest = store.get_latest_session(workspace_root="/tmp/ws")
        assert latest is not None and latest.id == sess.id

        msgs = store.load_messages(sess.id)
        assert [m.role for m in msgs] == [
            MessageRole.SYSTEM,
            MessageRole.USER,
            MessageRole.ASSISTANT,
        ]
        # Verify JSON storage only — no .db or .sqlite files anywhere
        assert list(sessions_dir.glob("*.json"))
        assert not list(tmp_path.rglob("*.db"))
        assert not list(tmp_path.rglob("*.sqlite*"))

    def test_fork_rename_search_compact_delete_and_checkpoint(self, tmp_path: Path) -> None:
        store = SessionStore(sessions_dir=tmp_path / "sessions")
        sess = store.create_session(
            active_model="gemini/gemini-2.0-flash",
            workspace_root="/tmp/ws",
            title="Database architecture",
            initial_messages=[ChatMessage(role=MessageRole.SYSTEM, content="sys")],
        )
        for i in range(6):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            store.append_message(
                sess.id, ChatMessage(role=role, content=f"Turn {i} pinecone notes")
            )

        cp = store.create_checkpoint(sess.id, reason="pre-edit", state={"target": "db.py"})
        assert cp is not None
        latest_cp = store.get_latest_checkpoint(sess.id)
        assert latest_cp is not None
        assert latest_cp.reason == "pre-edit"
        assert latest_cp.state["target"] == "db.py"

        forked = store.fork_session(sess.id, title="Alt branch")
        assert forked is not None
        assert forked.id != sess.id
        assert forked.message_count == 6

        assert store.rename_session(forked.id, "Renamed branch") is True
        renamed = store.get_session(forked.id)
        assert renamed is not None and renamed.title == "Renamed branch"

        hits = store.search_sessions("pinecone")
        assert len(hits) == 2

        ok, before_cnt, after_cnt = store.compact_session(
            sess.id, "Discussed pinecone.", keep_last=2
        )
        assert ok is True
        assert before_cnt == 7
        assert after_cnt == 4

        assert store.delete_session(sess.id) is True
        assert store.get_session(sess.id) is None

    def test_json_file_saver_persists_langgraph_interrupt_across_restarts(
        self, tmp_path: Path
    ) -> None:
        cp_dir = tmp_path / "checkpoints"

        class _DemoState(TypedDict):
            value: int
            approved: bool

        def _build_demo_graph(saver: JsonFileSaver) -> Any:
            builder = StateGraph(_DemoState)

            def step_a(state: _DemoState) -> dict[str, Any]:
                approved = interrupt({"question": "Proceed?"})
                return {"approved": bool(approved), "value": state.get("value", 0) + 1}

            builder.add_node("step_a", step_a)
            builder.add_edge(START, "step_a")
            builder.add_edge("step_a", END)
            return builder.compile(checkpointer=saver)

        g1 = _build_demo_graph(JsonFileSaver(cp_dir))
        cfg: Any = {"configurable": {"thread_id": "sess_persist"}}
        res1 = g1.invoke({"value": 41, "approved": False}, cfg)
        assert "__interrupt__" in res1
        assert (cp_dir / "sess_persist.json").exists()

        # Reload with a brand-new JsonFileSaver instance (simulating process restart)
        g2 = _build_demo_graph(JsonFileSaver(cp_dir))
        res2 = g2.invoke(Command(resume=True), cfg)
        assert res2["approved"] is True
        assert res2["value"] == 42


class TestChatEngineSessionSync:
    """Tests for ChatEngine persisting turns and model switches to SessionStore."""

    def test_send_turn_persists_to_store(self, tmp_path: Path) -> None:
        store = SessionStore(sessions_dir=tmp_path / "sessions")
        sys_msg = ChatMessage(role=MessageRole.SYSTEM, content="sys")
        sess = store.create_session(
            active_model="groq/llama-3.3-70b-versatile",
            workspace_root=str(tmp_path),
            initial_messages=[sys_msg],
        )

        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test", "gemini": "AIza_test"},
            initial_model="groq/llama-3.3-70b-versatile",
            session_store=store,
            session_id=sess.id,
            initial_messages=[sys_msg],
            checkpointer=JsonFileSaver(tmp_path / "checkpoints"),
        )

        fake_model = _FakeLangChainModel(
            responses=[
                AIMessage(
                    content="Saved!",
                    usage_metadata={"input_tokens": 10, "output_tokens": 3, "total_tokens": 13},
                )
            ]
        )

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(engine.send_turn("Hello persistence"))

        assert reply == "Saved!"
        persisted = store.get_session(sess.id)
        assert persisted is not None
        assert persisted.message_count == 2
        assert persisted.title == "Hello persistence"

        ok, _ = engine.switch_model("gemini/gemini-2.0-flash")
        assert ok is True
        updated = store.get_session(sess.id)
        assert updated is not None and updated.active_model == "gemini/gemini-2.0-flash"

    def test_slash_new_creates_fresh_session_and_context_window(self, tmp_path: Path) -> None:
        store = SessionStore(sessions_dir=tmp_path / "sessions")
        sys_msg = ChatMessage(role=MessageRole.SYSTEM, content="sys")
        first_sess = store.create_session(
            active_model="groq/llama-3.3-70b-versatile",
            workspace_root=str(tmp_path),
            title="Initial thread",
            initial_messages=[sys_msg],
        )
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/llama-3.3-70b-versatile",
            session_store=store,
            session_id=first_sess.id,
            initial_messages=[
                sys_msg,
                ChatMessage(role=MessageRole.USER, content="First question"),
                ChatMessage(role=MessageRole.ASSISTANT, content="First answer"),
            ],
            total_prompt_tokens=120,
            total_completion_tokens=45,
            workspace_root=tmp_path,
            checkpointer=JsonFileSaver(tmp_path / "checkpoints"),
        )
        store.append_message(
            first_sess.id, ChatMessage(role=MessageRole.USER, content="First question")
        )
        store.append_message(
            first_sess.id, ChatMessage(role=MessageRole.ASSISTANT, content="First answer")
        )
        engine.last_suggested_model = "gemini/gemini-3.8-flash"

        keep_running = _handle_slash_command("/new Fresh topic", engine)
        assert keep_running is True
        assert engine.session_id is not None
        assert engine.session_id != first_sess.id
        assert len(engine.messages) == 1
        assert engine.messages[0].role == MessageRole.SYSTEM
        assert engine.total_prompt_tokens == 0
        assert engine.total_completion_tokens == 0
        assert engine.last_suggested_model is None

        new_sess = store.get_session(engine.session_id)
        assert new_sess is not None
        assert new_sess.title == "Fresh topic"
        assert new_sess.message_count == 0
        assert new_sess.active_model == "groq/llama-3.3-70b-versatile"

        preserved = store.get_session(first_sess.id)
        assert preserved is not None
        assert preserved.title == "Initial thread"
        assert preserved.message_count == 2


class TestSessionCli:
    """Tests for valkyria session CLI subcommands."""

    def test_session_cli_lifecycle(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        cfg_file = tmp_path / "config.json"

        with (
            patch("valkyria.core.paths.get_sessions_dir", return_value=sessions_dir),
            patch("valkyria.sessions.store.get_sessions_dir", return_value=sessions_dir),
            patch("valkyria.core.config.get_config_path", return_value=cfg_file),
        ):
            runner = CliRunner()

            res_new = runner.invoke(cli, ["session", "new", "--title", "Sprint planning"])
            assert res_new.exit_code == 0, res_new.output
            assert "Sprint planning" in res_new.output

            res_list = runner.invoke(cli, ["session", "list"])
            assert res_list.exit_code == 0
            assert "Sprint planning" in res_list.output

            store = SessionStore(sessions_dir=sessions_dir)
            sid = store.list_sessions()[0].id

            res_show = runner.invoke(cli, ["session", "show", sid])
            assert res_show.exit_code == 0
            assert "Sprint planning" in res_show.output

            res_rename = runner.invoke(cli, ["session", "rename", sid, "Renamed plan"])
            assert res_rename.exit_code == 0

            res_fork = runner.invoke(cli, ["session", "fork", sid])
            assert res_fork.exit_code == 0
            assert "Fork of Renamed plan" in res_fork.output

            res_search = runner.invoke(cli, ["session", "search", "Renamed"])
            assert res_search.exit_code == 0
            assert sid in res_search.output

            res_del = runner.invoke(cli, ["session", "delete", sid, "--yes"])
            assert res_del.exit_code == 0
            assert "Deleted session" in res_del.output

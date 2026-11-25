"""Tests for Phase 7 session persistence, checkpoints, ChatEngine sync, and CLI."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from valkyrie.chat.engine import ChatEngine, _handle_slash_command
from valkyrie.chat.messages import ChatMessage, MessageRole, TokenUsage
from valkyrie.cli.main import cli
from valkyrie.core.config import ValkyrieConfig
from valkyrie.providers.registry import ModelRegistry
from valkyrie.sessions.store import SessionStore

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _FakeStreamResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self.status_code = 200

    async def __aenter__(self) -> _FakeStreamResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line


class TestSessionStore:
    """Tests for SQLite SessionStore operations."""

    def test_create_append_resume_and_prefix(self, tmp_path: Path) -> None:
        store = SessionStore(db_path=tmp_path / "sessions.db")
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

    def test_fork_rename_search_compact_delete_and_checkpoint(self, tmp_path: Path) -> None:
        store = SessionStore(db_path=tmp_path / "sessions.db")
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

        # Checkpoint
        cp = store.create_checkpoint(sess.id, reason="pre-edit", state={"target": "db.py"})
        assert cp is not None
        latest_cp = store.get_latest_checkpoint(sess.id)
        assert latest_cp is not None
        assert latest_cp.reason == "pre-edit"
        assert latest_cp.state["target"] == "db.py"

        # Fork
        forked = store.fork_session(sess.id, title="Alt branch")
        assert forked is not None
        assert forked.id != sess.id
        assert forked.message_count == 6

        # Rename
        assert store.rename_session(forked.id, "Renamed branch") is True
        renamed = store.get_session(forked.id)
        assert renamed is not None and renamed.title == "Renamed branch"

        # Search
        hits = store.search_sessions("pinecone")
        assert len(hits) == 2

        # Compact (system + 6 turns = 7 -> keep last 2 -> system + summary + 2 = 4)
        ok, before_cnt, after_cnt = store.compact_session(
            sess.id, "Discussed pinecone.", keep_last=2
        )
        assert ok is True
        assert before_cnt == 7
        assert after_cnt == 4

        # Delete
        assert store.delete_session(sess.id) is True
        assert store.get_session(sess.id) is None


class TestChatEngineSessionSync:
    """Tests for ChatEngine persisting turns and model switches to SessionStore."""

    def test_send_turn_persists_to_store(self, tmp_path: Path) -> None:
        store = SessionStore(db_path=tmp_path / "sessions.db")
        sys_msg = ChatMessage(role=MessageRole.SYSTEM, content="sys")
        sess = store.create_session(
            active_model="groq/llama-3.3-70b-versatile",
            workspace_root=str(tmp_path),
            initial_messages=[sys_msg],
        )

        engine = ChatEngine(
            config=ValkyrieConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test", "gemini": "AIza_test"},
            initial_model="groq/llama-3.3-70b-versatile",
            session_store=store,
            session_id=sess.id,
            initial_messages=[sys_msg],
        )

        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Saved!"},"finish_reason":"stop"}]}',
            'data: {"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":3}}',
            "data: [DONE]",
        ]
        fake_client = MagicMock()
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = None
        fake_client.stream.return_value = _FakeStreamResponse(sse_lines)

        with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
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
        store = SessionStore(db_path=tmp_path / "sessions.db")
        sys_msg = ChatMessage(role=MessageRole.SYSTEM, content="sys")
        first_sess = store.create_session(
            active_model="groq/llama-3.3-70b-versatile",
            workspace_root=str(tmp_path),
            title="Initial thread",
            initial_messages=[sys_msg],
        )
        engine = ChatEngine(
            config=ValkyrieConfig(),
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
    """Tests for valkyrie session CLI subcommands."""

    def test_session_cli_lifecycle(self, tmp_path: Path) -> None:
        db_file = tmp_path / "sessions.db"
        cfg_file = tmp_path / "config.json"

        with (
            patch("valkyrie.core.paths.get_sessions_db_path", return_value=db_file),
            patch("valkyrie.sessions.store.get_sessions_db_path", return_value=db_file),
            patch("valkyrie.core.config.get_config_path", return_value=cfg_file),
        ):
            runner = CliRunner()

            res_new = runner.invoke(cli, ["session", "new", "--title", "Sprint planning"])
            assert res_new.exit_code == 0, res_new.output
            assert "Sprint planning" in res_new.output

            res_list = runner.invoke(cli, ["session", "list"])
            assert res_list.exit_code == 0
            assert "Sprint planning" in res_list.output

            store = SessionStore(db_path=db_file)
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

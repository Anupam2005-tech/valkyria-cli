"""Tests for local machine CRUD tools, DuckDuckGo search, & LangGraph agent tool loop."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

from valkyria.chat.engine import ChatEngine, _handle_slash_command
from valkyria.core.config import ValkyriaConfig
from valkyria.providers.registry import ModelRegistry
from valkyria.rag.embeddings import resolve_pinecone_api_key, resolve_pinecone_config
from valkyria.tools.registry import AgentToolset

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _FakeToolChatModel(BaseChatModel):
    scripted: list[list[AIMessageChunk]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "fake-tool-model"

    def bind_tools(self, tools: Any, **kwargs: Any) -> _FakeToolChatModel:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        chunks = self.scripted.pop(0)
        merged = chunks[0]
        for nxt in chunks[1:]:
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
        chunks = self.scripted.pop(0)
        for chunk in chunks:
            if run_manager and chunk.text:
                await run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            yield ChatGenerationChunk(message=chunk)


class TestAppOwnedPineconeEnv:
    """Tests for loading Pinecone credentials & index automatically from app .env."""

    def test_resolves_from_app_root_env_outside_workspace(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        app_root = tmp_path / "app"
        app_root.mkdir()
        (app_root / ".env").write_text(
            "PINECONE_API_KEY=pcsk_app_owner_999\nPINECONE_INDEX=owner-index\n"
        )
        other_ws = tmp_path / "user_project"
        other_ws.mkdir()

        monkeypatch.setattr("valkyria.rag.embeddings._APP_ROOT", app_root)
        cfg = ValkyriaConfig()

        assert resolve_pinecone_api_key(other_ws) == "pcsk_app_owner_999"
        resolved_cfg = resolve_pinecone_config(cfg, other_ws)
        assert resolved_cfg.index_name == "owner-index"


class TestLocalMachineCrudAndWebTools:
    """Tests for create, read, update, delete, list, search, & LangChain DuckDuckGo."""

    def test_crud_lifecycle_and_safety_blocks(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        toolset = AgentToolset(workspace_root=ws)

        ok, msg = toolset.execute(
            "write_file",
            {"path": "notes/hello.md", "content": "# Hello\nInitial line\n"},
        )
        assert ok is True
        assert "Created" in msg
        target = ws / "notes" / "hello.md"
        assert target.exists()

        ok_r, txt = toolset.execute("read_file", {"path": "notes/hello.md"})
        assert ok_r is True
        assert "Initial line" in txt

        ok_e, emsg = toolset.execute(
            "edit_file",
            {
                "path": "notes/hello.md",
                "target": "Initial line",
                "replacement": "Updated line",
            },
        )
        assert ok_e is True
        assert "1 replacement(s)" in emsg
        assert "Updated line" in target.read_text()

        ok_l, ltxt = toolset.execute("list_directory", {"path": "notes"})
        assert ok_l is True
        assert "hello.md" in ltxt

        ok_s, stxt = toolset.execute("search_files", {"query": "Updated"})
        assert ok_s is True
        assert "notes/hello.md" in stxt

        ok_d, dmsg = toolset.execute("delete_file", {"path": "notes/hello.md"})
        assert ok_d is True
        assert "Deleted" in dmsg
        assert not target.exists()

        ok_sec, sec_msg = toolset.execute("read_file", {"path": "/etc/passwd"})
        assert ok_sec is False
        assert "Blocked" in sec_msg

        (ws / ".env").write_text("PINECONE_API_KEY=secret\n")
        ok_env, env_msg = toolset.execute("read_file", {"path": ".env"})
        assert ok_env is False
        assert "Blocked" in env_msg

    def test_langchain_duckduckgo_web_search_and_schemas(self, tmp_path: Path) -> None:
        toolset = AgentToolset(workspace_root=tmp_path)
        openai_specs = toolset.openai_tools()
        gemini_decls = toolset.gemini_declarations()
        assert any(s["function"]["name"] == "web_search" for s in openai_specs)
        assert any(d["name"] == "write_file" for d in gemini_decls)

        fake_results = [
            {
                "title": "Python 3.13 Release",
                "link": "https://www.python.org/",
                "snippet": "Latest Python runtime details.",
            }
        ]
        with patch("valkyria.tools.web_search.run_duckduckgo_search", return_value=fake_results):
            ok, out = toolset.execute("web_search", {"query": "python 3.13"})
        assert ok is True
        assert "Python 3.13 Release" in out
        assert "https://www.python.org/" in out


class TestAgentToolLoop:
    """End-to-end LangGraph tool-calling loop across Gemini, Groq, and safety-gate interrupts."""

    def test_gemini_creates_file_via_tool_call_loop(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        downloads_file = tmp_path / "Downloads" / "hello.md"

        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"gemini": "AIza_test"},
            initial_model="gemini/gemini-3.8-flash",
            workspace_root=ws,
            auto_approve_tools=True,
        )

        fake_model = _FakeToolChatModel(
            scripted=[
                [
                    AIMessageChunk(
                        content="",
                        tool_calls=[
                            {
                                "id": "gemini_call_1",
                                "name": "write_file",
                                "args": {
                                    "path": str(downloads_file),
                                    "content": "# Hello from Valkyria\n",
                                },
                            }
                        ],
                        usage_metadata={
                            "input_tokens": 40,
                            "output_tokens": 12,
                            "total_tokens": 52,
                        },
                    )
                ],
                [
                    AIMessageChunk(
                        content="Created hello.md!",
                        usage_metadata={"input_tokens": 75, "output_tokens": 8, "total_tokens": 83},
                    )
                ],
            ]
        )

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(engine.send_turn("in the download folder create a hello.md file"))

        assert reply == "Created hello.md!"
        assert downloads_file.exists()
        assert downloads_file.read_text() == "# Hello from Valkyria\n"

    def test_slash_web_and_slash_auto_commands(self, tmp_path: Path) -> None:
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/openai/gpt-oss-120b",
            workspace_root=tmp_path,
        )
        assert _handle_slash_command("/auto on", engine) is True
        assert engine.auto_approve_tools is True
        assert _handle_slash_command("/auto off", engine) is True
        assert engine.auto_approve_tools is False

        fake_results = [
            {"title": "DuckDuckGo", "link": "https://duckduckgo.com", "snippet": "Private search"}
        ]
        with patch("valkyria.chat.engine.run_duckduckgo_search", return_value=fake_results):
            assert _handle_slash_command("/web valkyria cli", engine) is True

    def test_openai_groq_tool_call_delta_assembly(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "note.txt").write_text("alpha beta")
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/openai/gpt-oss-120b",
            workspace_root=ws,
            auto_approve_tools=True,
        )

        fake_model = _FakeToolChatModel(
            scripted=[
                [
                    AIMessageChunk(
                        content="",
                        tool_call_chunks=[
                            {
                                "index": 0,
                                "id": "call_1",
                                "name": "edit_",
                                "args": '{"path": "note.txt",',
                            }
                        ],
                    ),
                    AIMessageChunk(
                        content="",
                        tool_call_chunks=[
                            {
                                "index": 0,
                                "id": None,
                                "name": "file",
                                "args": ' "target": "beta", "replacement": "gamma"}',
                            }
                        ],
                        usage_metadata={
                            "input_tokens": 20,
                            "output_tokens": 10,
                            "total_tokens": 30,
                        },
                    ),
                ],
                [
                    AIMessageChunk(
                        content="Updated note.txt to alpha gamma.",
                        usage_metadata={"input_tokens": 35, "output_tokens": 8, "total_tokens": 43},
                    )
                ],
            ]
        )

        with patch("valkyria.chat.clients.build_chat_model", return_value=fake_model):
            reply = asyncio.run(engine.send_turn("change beta to gamma in note.txt"))

        assert reply == "Updated note.txt to alpha gamma."
        assert (ws / "note.txt").read_text() == "alpha gamma"

    def test_tool_safety_gate_interrupts_and_respects_denial(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        target = ws / "blocked.txt"

        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/openai/gpt-oss-120b",
            workspace_root=ws,
            auto_approve_tools=False,
        )
        fake_model = _FakeToolChatModel(
            scripted=[
                [
                    AIMessageChunk(
                        content="",
                        tool_calls=[
                            {
                                "id": "call_deny_1",
                                "name": "write_file",
                                "args": {"path": "blocked.txt", "content": "should not write"},
                            }
                        ],
                    )
                ],
                [AIMessageChunk(content="Understood, file was not created.")],
            ]
        )

        with (
            patch("valkyria.chat.clients.build_chat_model", return_value=fake_model),
            patch.object(
                engine,
                "_prompt_tool_batch_approval",
                return_value={"approved_ids": [], "denied_ids": ["call_deny_1"]},
            ) as mock_gate,
        ):
            reply = asyncio.run(engine.send_turn("create blocked.txt"))

        mock_gate.assert_called_once()
        assert not target.exists()
        assert reply == "Understood, file was not created."


class TestRunCommandAndPkgTools:
    """Tests for sandboxed run_command, pkg_install, and /run + /pkg slash commands."""

    def test_run_command_executes_and_captures_output(self, tmp_path: Path) -> None:
        toolset = AgentToolset(workspace_root=tmp_path, auto_approve=True)
        openai_specs = toolset.openai_tools()
        gemini_decls = toolset.gemini_declarations()
        assert any(s["function"]["name"] == "run_command" for s in openai_specs)
        assert any(d["name"] == "pkg_install" for d in gemini_decls)

        ok, out = toolset.execute("run_command", {"command": "echo valkyria_ok"})
        assert ok is True
        assert "[exit 0]" in out
        assert "valkyria_ok" in out

    def test_run_command_blocks_denylist_even_with_auto_approve(self, tmp_path: Path) -> None:
        toolset = AgentToolset(workspace_root=tmp_path, auto_approve=True)
        ok, out = toolset.execute("run_command", {"command": "rm -rf /"})
        assert ok is True
        assert "Error:" in out
        assert "blocked pattern" in out

    def test_run_command_respects_user_decline(self, tmp_path: Path) -> None:
        toolset = AgentToolset(
            workspace_root=tmp_path,
            confirm_fn=lambda action, target, preview: False,
            auto_approve=False,
        )
        ok, out = toolset.execute("run_command", {"command": "echo should_not_run"})
        assert ok is True
        assert "User declined" in out

    def test_pkg_install_resolves_and_runs(self, tmp_path: Path) -> None:
        from valkyria.tools.pkg_manager import _resolve_command

        assert _resolve_command("pip", "install", ["httpx", "rich"]) == "pip install httpx rich"
        assert _resolve_command("npm", "install", ["lodash"]) == "npm install lodash"
        assert _resolve_command("uv", "list", []) == "uv pip list"

        toolset = AgentToolset(workspace_root=tmp_path, auto_approve=True)
        fake_proc = MagicMock(returncode=0, stdout="Successfully installed httpx", stderr="")
        with patch("valkyria.tools.run_command.subprocess.run", return_value=fake_proc) as mock_run:
            ok, out = toolset.execute(
                "pkg_install",
                {"manager": "pip", "action": "install", "packages": ["httpx"]},
            )
        assert ok is True
        assert "Successfully installed httpx" in out
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == "pip install httpx"

    def test_slash_run_pkg_and_auto_propagation(self, tmp_path: Path) -> None:
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/openai/gpt-oss-120b",
            workspace_root=tmp_path,
            auto_approve_tools=False,
        )
        assert engine.toolset.auto_approve is False
        _handle_slash_command("/auto on", engine)
        assert engine.auto_approve_tools is True
        assert engine.toolset.auto_approve is True

        fake_proc = MagicMock(returncode=0, stdout="hello_slash", stderr="")
        with patch("valkyria.tools.run_command.subprocess.run", return_value=fake_proc) as mock_run:
            keep_going = _handle_slash_command("/run echo hello_slash", engine)
            assert keep_going is True
            assert mock_run.call_args.args[0] == "echo hello_slash"

            keep_going_pkg = _handle_slash_command("/pkg pip install rich", engine)
            assert keep_going_pkg is True
            assert mock_run.call_args.args[0] == "pip install rich"

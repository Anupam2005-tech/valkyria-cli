"""Tests for local machine CRUD tools, LangChain DuckDuckGo web search, & agent tool loop."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from valkyrie.chat.engine import ChatEngine, _handle_slash_command
from valkyrie.core.config import ValkyrieConfig
from valkyrie.providers.registry import ModelRegistry
from valkyrie.rag.embeddings import resolve_pinecone_api_key, resolve_pinecone_config
from valkyrie.tools.registry import AgentToolset

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path


class _FakeStreamResponse:
    def __init__(self, lines: list[str], status_code: int = 200) -> None:
        self._lines = lines
        self.status_code = status_code

    async def __aenter__(self) -> _FakeStreamResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def aread(self) -> bytes:
        return b""

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line


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

        monkeypatch.setattr("valkyrie.rag.embeddings._APP_ROOT", app_root)
        cfg = ValkyrieConfig()

        assert resolve_pinecone_api_key(other_ws) == "pcsk_app_owner_999"
        resolved_cfg = resolve_pinecone_config(cfg, other_ws)
        assert resolved_cfg.index_name == "owner-index"


class TestLocalMachineCrudAndWebTools:
    """Tests for create, read, update, delete, list, search, & LangChain DuckDuckGo."""

    def test_crud_lifecycle_and_safety_blocks(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        toolset = AgentToolset(workspace_root=ws)

        # Create file (including parent dirs)
        ok, msg = toolset.execute(
            "write_file",
            {"path": "notes/hello.md", "content": "# Hello\nInitial line\n"},
        )
        assert ok is True
        assert "Created" in msg
        target = ws / "notes" / "hello.md"
        assert target.exists()

        # Read file
        ok_r, txt = toolset.execute("read_file", {"path": "notes/hello.md"})
        assert ok_r is True
        assert "Initial line" in txt

        # Update / edit file
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

        # List directory & search files
        ok_l, ltxt = toolset.execute("list_directory", {"path": "notes"})
        assert ok_l is True
        assert "hello.md" in ltxt

        ok_s, stxt = toolset.execute("search_files", {"query": "Updated"})
        assert ok_s is True
        assert "notes/hello.md" in stxt

        # Delete file
        ok_d, dmsg = toolset.execute("delete_file", {"path": "notes/hello.md"})
        assert ok_d is True
        assert "Deleted" in dmsg
        assert not target.exists()

        # Protected system & credential paths must be blocked
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
        with patch("valkyrie.tools.web_search.run_duckduckgo_search", return_value=fake_results):
            ok, out = toolset.execute("web_search", {"query": "python 3.13"})
        assert ok is True
        assert "Python 3.13 Release" in out
        assert "https://www.python.org/" in out


class TestAgentToolLoop:
    """End-to-end streaming tool call loop across Gemini and OpenAI/Groq SSE."""

    def test_gemini_creates_file_via_tool_call_loop(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        downloads_file = tmp_path / "Downloads" / "hello.md"

        engine = ChatEngine(
            config=ValkyrieConfig(),
            registry=ModelRegistry(),
            api_keys={"gemini": "AIza_test"},
            initial_model="gemini/gemini-3.8-flash",
            workspace_root=ws,
            auto_approve_tools=True,
        )

        # Turn 1: Gemini emits a functionCall to write_file
        step1_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "write_file",
                                    "args": {
                                        "path": str(downloads_file),
                                        "content": "# Hello from Valkyrie\n",
                                    },
                                }
                            }
                        ]
                    }
                }
            ],
            "usageMetadata": {"promptTokenCount": 40, "candidatesTokenCount": 12},
        }
        step1_lines = [f"data: {json.dumps(step1_payload)}"]
        # Turn 2: Gemini responds after observing tool execution result
        step2_payload = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Created hello.md!"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {"promptTokenCount": 75, "candidatesTokenCount": 8},
        }
        step2_lines = [f"data: {json.dumps(step2_payload)}"]

        fake_client = MagicMock()
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = None
        fake_client.stream.side_effect = [
            _FakeStreamResponse(step1_lines),
            _FakeStreamResponse(step2_lines),
        ]

        with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
            reply = asyncio.run(engine.send_turn("in the download folder create a hello.md file"))

        assert reply == "Created hello.md!"
        assert downloads_file.exists()
        assert downloads_file.read_text() == "# Hello from Valkyrie\n"

    def test_slash_web_and_slash_auto_commands(self, tmp_path: Path) -> None:
        engine = ChatEngine(
            config=ValkyrieConfig(),
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
        with patch("valkyrie.chat.engine.run_duckduckgo_search", return_value=fake_results):
            assert _handle_slash_command("/web valkyrie cli", engine) is True

    def test_openai_groq_tool_call_delta_assembly(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "note.txt").write_text("alpha beta")
        engine = ChatEngine(
            config=ValkyrieConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/openai/gpt-oss-120b",
            workspace_root=ws,
            auto_approve_tools=True,
        )

        # Simulated chunked tool_call deltas followed by final answer
        step1_lines = [
            (
                'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1",'
                '"function":{"name":"edit_","arguments":"{\\"path\\": \\"note.txt\\","}}]}}]}'
            ),
            (
                'data: {"choices":[{"delta":{"tool_calls":[{"index":0,'
                '"function":{"name":"file","arguments":"\\"target\\": \\"beta\\", '
                '\\"replacement\\": \\"gamma\\"}"}}]},"finish_reason":"tool_calls"}]}'
            ),
            'data: {"choices":[],"usage":{"prompt_tokens":20,"completion_tokens":10}}',
            "data: [DONE]",
        ]
        step2_lines = [
            (
                'data: {"choices":[{"delta":{"content":"Updated note.txt to alpha gamma."},'
                '"finish_reason":"stop"}]}'
            ),
            'data: {"choices":[],"usage":{"prompt_tokens":35,"completion_tokens":8}}',
            "data: [DONE]",
        ]
        fake_client = MagicMock()
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = None
        fake_client.stream.side_effect = [
            _FakeStreamResponse(step1_lines),
            _FakeStreamResponse(step2_lines),
        ]

        with patch("valkyrie.chat.clients.httpx.AsyncClient", return_value=fake_client):
            reply = asyncio.run(engine.send_turn("change beta to gamma in note.txt"))

        assert reply == "Updated note.txt to alpha gamma."
        assert (ws / "note.txt").read_text() == "alpha gamma"


class TestRunCommandAndPkgTools:
    """Tests for sandboxed run_command, pkg_install, and /run + /pkg slash commands."""

    def test_run_command_executes_and_captures_output(self, tmp_path: Path) -> None:
        toolset = AgentToolset(workspace_root=tmp_path, auto_approve=True)
        openai_specs = toolset.openai_tools()
        gemini_decls = toolset.gemini_declarations()
        assert any(s["function"]["name"] == "run_command" for s in openai_specs)
        assert any(d["name"] == "pkg_install" for d in gemini_decls)

        ok, out = toolset.execute("run_command", {"command": "echo valkyrie_ok"})
        assert ok is True
        assert "[exit 0]" in out
        assert "valkyrie_ok" in out

    def test_run_command_blocks_denylist_even_with_auto_approve(self, tmp_path: Path) -> None:
        toolset = AgentToolset(workspace_root=tmp_path, auto_approve=True)
        ok, out = toolset.execute("run_command", {"command": "rm -rf /"})
        assert ok is True  # tool catches PermissionError and returns Error string
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
        from valkyrie.tools.pkg_manager import _resolve_command

        assert _resolve_command("pip", "install", ["httpx", "rich"]) == "pip install httpx rich"
        assert _resolve_command("npm", "install", ["lodash"]) == "npm install lodash"
        assert _resolve_command("uv", "list", []) == "uv pip list"

        toolset = AgentToolset(workspace_root=tmp_path, auto_approve=True)
        fake_proc = MagicMock(returncode=0, stdout="Successfully installed httpx", stderr="")
        with patch("valkyrie.tools.run_command.subprocess.run", return_value=fake_proc) as mock_run:
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
            config=ValkyrieConfig(),
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
        with patch("valkyrie.tools.run_command.subprocess.run", return_value=fake_proc) as mock_run:
            keep_going = _handle_slash_command("/run echo hello_slash", engine)
            assert keep_going is True
            assert mock_run.call_args.args[0] == "echo hello_slash"

            keep_going_pkg = _handle_slash_command("/pkg pip install rich", engine)
            assert keep_going_pkg is True
            assert mock_run.call_args.args[0] == "pip install rich"

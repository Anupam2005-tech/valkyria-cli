"""Tests for Phase 8 workspace detection, slash command registry, @ completer, and /compact."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.document import Document

from valkyrie.chat.commands import SlashCommandRegistry, ValkyrieCompleter
from valkyrie.chat.engine import ChatEngine, _handle_slash_command, build_command_registry
from valkyrie.chat.messages import ChatMessage, MessageRole
from valkyrie.core.config import ValkyrieConfig
from valkyrie.core.workspace import (
    detect_workspace_root,
    list_workspace_files,
    resolve_workspace_path,
)
from valkyrie.providers.registry import ModelRegistry
from valkyrie.sessions.store import SessionStore

if TYPE_CHECKING:
    from pathlib import Path


class TestWorkspaceAwareness:
    """Tests for workspace root detection, file listing, and path scoping."""

    def test_detect_workspace_root_priority(self, tmp_path: Path) -> None:
        # Fallback to start_dir when no markers
        plain = tmp_path / "plain" / "sub"
        plain.mkdir(parents=True)
        assert detect_workspace_root(plain) == plain.resolve()

        # .git marker wins over fallback
        git_repo = tmp_path / "repo"
        (git_repo / ".git").mkdir(parents=True)
        nested = git_repo / "src" / "pkg"
        nested.mkdir(parents=True)
        assert detect_workspace_root(nested) == git_repo.resolve()

        # .valkyrie marker wins over .git
        (nested / ".valkyrie").mkdir()
        assert detect_workspace_root(nested) == nested.resolve()

    def test_list_and_resolve_workspace_files(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("ignored")
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        (tmp_path / ".venv" / "bin" / "python").write_text("ignored")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("print('ok')")
        (tmp_path / "readme.md").write_text("# hi")

        files = list_workspace_files(tmp_path)
        assert files == ["readme.md", "src/app.py"]

        resolved = resolve_workspace_path(tmp_path, "src/app.py")
        assert resolved == (tmp_path / "src" / "app.py").resolve()
        assert resolve_workspace_path(tmp_path, "../escape.txt") is None


class TestSlashCommandsAndCompleter:
    """Tests for SlashCommandRegistry prefix filtering, dev flags, and @ completion."""

    def test_prefix_filter_and_feature_flags(self, tmp_path: Path) -> None:
        engine = ChatEngine(
            config=ValkyrieConfig(),
            registry=ModelRegistry(),
            api_keys={},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=tmp_path,
        )
        reg = build_command_registry(engine)

        # Prefix filter for /m returns /model
        matches = reg.filter_prefix("/m")
        assert [c.name for c in matches] == ["/model"]

        # Alias /quit resolves to /exit
        assert reg.resolve("/quit") is not None
        assert reg.resolve("/quit").name == "/exit"  # type: ignore[union-attr]

        # Live Phase 9 commands are executable; upcoming Beta commands are hidden
        normal_help_names = {c.name for c in reg.help_commands()}
        assert "/index" in normal_help_names
        assert "/plan" not in normal_help_names
        assert reg.resolve("/plan") is None

        # Shown in /help only in dev builds, still not executable
        dev_reg = build_command_registry(
            ChatEngine(
                config=ValkyrieConfig(feature_flags={"dev_mode": True}),
                registry=ModelRegistry(),
                api_keys={},
                initial_model="groq/llama-3.3-70b-versatile",
                workspace_root=tmp_path,
            )
        )
        dev_help_names = {c.name for c in dev_reg.help_commands()}
        assert "/plan" in dev_help_names
        assert dev_reg.resolve("/plan") is None

    def test_completer_slash_and_at_paths(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "cli.py").write_text("pass")
        (tmp_path / "notes.md").write_text("hi")

        engine = ChatEngine(
            config=ValkyrieConfig(),
            registry=ModelRegistry(),
            api_keys={},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=tmp_path,
        )
        reg: SlashCommandRegistry = build_command_registry(engine)
        completer = ValkyrieCompleter(reg, tmp_path)

        slash_comps = list(completer.get_completions(Document("/co"), None))
        assert [c.text for c in slash_comps] == ["/compact"]

        path_comps = list(completer.get_completions(Document("check @src/"), None))
        assert [c.text for c in path_comps] == ["@src/cli.py"]

        model_comps = [c.text for c in completer.get_completions(Document("/model g"), None)]
        assert "groq" in model_comps
        assert "gemini" in model_comps


class TestInChatCompact:
    """Tests for /compact inside ChatEngine with SessionStore."""

    def test_compact_command_updates_engine_and_store(self, tmp_path: Path) -> None:
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
            api_keys={},
            initial_model="groq/llama-3.3-70b-versatile",
            session_store=store,
            session_id=sess.id,
            initial_messages=[sys_msg],
            workspace_root=tmp_path,
        )
        for i in range(6):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            msg = ChatMessage(role=role, content=f"Turn {i} details")
            engine.messages.append(msg)
            store.append_message(sess.id, msg)

        assert _handle_slash_command("/compact 2", engine) is True
        # system + compacted summary + last 2 turns = 4 messages
        assert len(engine.messages) == 4
        assert "Compacted conversation summary" in engine.messages[1].content
        assert len(store.load_messages(sess.id)) == 4

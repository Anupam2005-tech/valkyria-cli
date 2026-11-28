"""
Slash command registry and prompt-toolkit completer (`/`, `/model <id>`, `@path`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from prompt_toolkit.completion import Completer, Completion

from valkyria.core.workspace import list_workspace_files
from valkyria.providers.registry import PROVIDERS

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

    from prompt_toolkit.document import Document

    from valkyria.providers.registry import ModelRegistry


def is_dev_build(feature_flags: dict[str, bool] | None = None) -> bool:
    """Return True when running in a development build or with dev_mode enabled."""
    if os.environ.get("VALKYRIA_DEV", "").strip().lower() in ("1", "true", "yes"):
        return True
    return bool(feature_flags and feature_flags.get("dev_mode", False))


@dataclass
class SlashCommand:
    """Definition of a chat slash command."""

    name: str  # e.g. "/help"
    usage: str
    description: str
    handler: Callable[[list[str]], bool] | None = None
    aliases: tuple[str, ...] = ()
    feature_flag: str | None = None
    upcoming: bool = False


class SlashCommandRegistry:
    """Registry supporting prefix filtering, feature gating, and execution."""

    def __init__(self, feature_flags: dict[str, bool] | None = None) -> None:
        self.feature_flags = feature_flags or {}
        self._commands: dict[str, SlashCommand] = {}

    def register(self, cmd: SlashCommand) -> None:
        """Register a slash command."""
        self._commands[cmd.name.lower()] = cmd

    def is_executable(self, cmd: SlashCommand) -> bool:
        """Return True if a command is active and can be executed."""
        if cmd.upcoming:
            return False
        if cmd.feature_flag and not self.feature_flags.get(cmd.feature_flag, False):
            return False
        return cmd.handler is not None

    def executable_commands(self) -> list[SlashCommand]:
        """Return all active executable commands sorted by name."""
        return sorted(
            (c for c in self._commands.values() if self.is_executable(c)),
            key=lambda c: c.name,
        )

    def help_commands(self) -> list[SlashCommand]:
        """Return commands to display in /help (including upcoming only in dev builds)."""
        dev = is_dev_build(self.feature_flags)
        items = [
            c for c in self._commands.values() if self.is_executable(c) or (dev and c.upcoming)
        ]
        return sorted(items, key=lambda c: c.name)

    def filter_prefix(self, prefix: str) -> list[SlashCommand]:
        """Filter executable commands matching a `/` prefix."""
        needle = prefix.strip().lower()
        if not needle.startswith("/"):
            needle = "/" + needle
        results: list[SlashCommand] = []
        for cmd in self.executable_commands():
            if cmd.name.startswith(needle) or any(a.startswith(needle) for a in cmd.aliases):
                results.append(cmd)
        return results

    def resolve(self, name: str) -> SlashCommand | None:
        """Find an executable command by exact name or alias."""
        needle = name.strip().lower()
        for cmd in self.executable_commands():
            if cmd.name == needle or needle in cmd.aliases:
                return cmd
        return None


class ValkyriaCompleter(Completer):
    """Autocomplete `/` slash commands, `/model` targets/providers, and `@` workspace paths."""

    def __init__(
        self,
        registry: SlashCommandRegistry,
        workspace_root: Path,
        model_registry: ModelRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.workspace_root = workspace_root
        self.model_registry = model_registry
        self._cached_files: list[str] | None = None

    def _get_files(self) -> list[str]:
        if self._cached_files is None:
            self._cached_files = list_workspace_files(self.workspace_root)
        return self._cached_files

    def refresh_files(self) -> None:
        """Invalidate cached workspace file list."""
        self._cached_files = None

    def _model_completions(self, text: str) -> Iterable[Completion]:
        parts = text.split(" ")
        last = parts[-1].lower()
        subcmds = [
            ("list", "list models (optionally filter by provider)"),
            ("pick", "interactive numbered model selector"),
            ("refresh", "fetch live catalogs from providers"),
            ("use", "switch to a model by ID"),
        ]
        if len(parts) == 2:
            for sub, desc in subcmds:
                if not last or sub.startswith(last):
                    yield Completion(
                        sub,
                        start_position=-len(last),
                        display=sub,
                        display_meta=desc,
                    )
            for pkey, pobj in PROVIDERS.items():
                if not last or pkey.startswith(last):
                    yield Completion(
                        pkey,
                        start_position=-len(last),
                        display=pkey,
                        display_meta=f"filter {pobj.name} models",
                    )

        if self.model_registry is None:
            return

        # Suggest active models matching typed fragment (after /model or /model list/use/pick)
        provider_hint = (
            parts[1].lower()
            if len(parts) >= 3 and parts[1].lower() in PROVIDERS
            else None
        )
        candidates = self.model_registry.list_models(provider=provider_hint)
        for m in candidates:
            if not m.is_active:
                continue
            if not last or last in m.qualified_id.lower():
                ctx = f"{m.context_window // 1000}k" if m.context_window else "?"
                yield Completion(
                    m.qualified_id,
                    start_position=-len(last),
                    display=m.qualified_id,
                    display_meta=f"{ctx} ctx",
                )

    def _account_completions(self, text: str) -> Iterable[Completion]:
        parts = text.split(" ")
        if len(parts) != 2:
            return
        last = parts[1].lower()
        subcmds = [
            ("status", "show active signed-in account details"),
            ("switch", "switch to another Google account"),
            ("delete", "permanently delete account and remote vault"),
            ("login", "sign in with Google via browser"),
            ("logout", "sign out locally without deleting account"),
        ]
        for sub, desc in subcmds:
            if not last or sub.startswith(last):
                yield Completion(
                    sub,
                    start_position=-len(last),
                    display=sub,
                    display_meta=desc,
                )

    def get_completions(
        self, document: Document, complete_event: object
    ) -> Iterable[Completion]:
        text = document.text_before_cursor

        # 1. Slash command completion when line starts with / and no space yet
        if text.startswith("/") and " " not in text:
            matches = self.registry.filter_prefix(text)
            for cmd in matches:
                yield Completion(
                    cmd.name,
                    start_position=-len(text),
                    display=cmd.name,
                    display_meta=cmd.description,
                )
            return

        # 2. /model (or /m) arguments completion (providers, subcommands, and active models)
        if text.lower().startswith(("/model ", "/m ")):
            yield from self._model_completions(text)
            return

        # 3. /account (or /acc, /auth) subcommands completion
        if text.lower().startswith(("/account ", "/acc ", "/auth ")):
            yield from self._account_completions(text)
            return

        # 3. @path completion anywhere in the prompt
        word = document.get_word_before_cursor(WORD=True)
        if word.startswith("@"):
            needle = word[1:].lower()
            for rel_path in self._get_files():
                if needle in rel_path.lower():
                    yield Completion(
                        f"@{rel_path}",
                        start_position=-len(word),
                        display=f"@{rel_path}",
                    )

"""
Chat engine — conversation state, context accounting, provider filtering, /model switching, & REPL.
"""

from __future__ import annotations

import asyncio
import re
import sys
from typing import TYPE_CHECKING

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from valkyrie.chat.clients import ChatStreamError, stream_chat_completion
from valkyrie.chat.commands import SlashCommand, SlashCommandRegistry, ValkyrieCompleter
from valkyrie.chat.messages import (
    ChatMessage,
    ContextBudget,
    MessageRole,
    estimate_messages_tokens,
)
from valkyrie.chat.renderer import render_agent_stream
from valkyrie.core.cards import render_tool_card
from valkyrie.core.console import (
    console,
    print_error,
    print_info,
    print_kv,
    print_rule,
    print_success,
    print_warning,
    render_meter,
)
from valkyrie.core.workspace import detect_workspace_root, list_workspace_files
from valkyrie.providers.registry import PROVIDERS, ModelRegistry
from valkyrie.rag.embeddings import resolve_pinecone_api_key
from valkyrie.rag.files import read_workspace_file
from valkyrie.rag.pipeline import (
    format_rag_context,
    index_workspace_path,
    search_workspace_rag,
)
from valkyrie.tools.registry import AgentToolset
from valkyrie.tools.web_search import run_duckduckgo_search

if TYPE_CHECKING:
    from pathlib import Path

    from valkyrie.core.config import ValkyrieConfig
    from valkyrie.providers.base import ModelInfo
    from valkyrie.rag.pinecone_store import PineconeRagStore
    from valkyrie.sessions.store import SessionRecord, SessionStore

_AT_PATH_RE = re.compile(r"(?<!\S)@([A-Za-z0-9_.\-/]+)")

_PROMPT_STYLE = Style.from_dict(
    {
        "completion-menu": "bg:#11161f #c9d1d9",
        "completion-menu.completion": "bg:#11161f #c9d1d9",
        "completion-menu.completion.current": "bg:#00f5d4 #0a0e14 bold",
        "completion-menu.meta": "bg:#11161f #8b949e",
        "completion-menu.meta.current": "bg:#00f5d4 #0a0e14",
        "scrollbar.background": "bg:#0d1117",
        "scrollbar.button": "bg:#30363d",
        "bottom-toolbar": "bg:#0d1117 #8b949e",
    }
)


def build_system_prompt(
    config: ValkyrieConfig,
    workspace_root: Path | None = None,
) -> str:
    """Build an editorial agent system prompt describing available local & web tools."""
    from pathlib import Path as _Path

    ws_hint = str(workspace_root) if workspace_root else "."
    home_downloads = str(_Path.home() / "Downloads")
    lines = [
        "You are Valkyrie, a precise, capable terminal AI agent.",
        "Keep answers direct, accurate, and formatted cleanly in Markdown.",
        "You have real tools to work on the user's local machine and search the web:",
        "- write_file / edit_file / delete_file / read_file / list_directory / search_files",
        f"  (Workspace root: {ws_hint}; user Downloads folder: {home_downloads})",
        "- web_search (live DuckDuckGo search via LangChain)",
        "- run_command (execute shell commands in the workspace; requires user approval)",
        "- pkg_install (install/uninstall/list packages via pip, npm, cargo, brew, apt, etc.)",
        "When the user asks you to create, read, update, change, or delete a file or search "
        "the web, call the appropriate tool(s) immediately and report the exact paths/URLs.",
        "When the user asks you to install software, download a package, run a command, "
        "execute tests, build a project, or perform any terminal operation, call run_command "
        "or pkg_install as appropriate. Always show the command before it runs.",
    ]
    profile_parts: list[str] = []
    if config.profile.name:
        profile_parts.append(f"name={config.profile.name}")
    if config.profile.profession:
        profile_parts.append(f"profession={config.profile.profession}")
    if config.profile.expertise:
        profile_parts.append(f"expertise={config.profile.expertise}")
    if profile_parts:
        lines.append("User context: " + ", ".join(profile_parts) + ".")
    return "\n".join(lines)


_MAX_TOOL_STEPS = 8


class ChatEngine:
    """Manages an interactive chat conversation, model state, tools, and context budget."""

    def __init__(
        self,
        *,
        config: ValkyrieConfig,
        registry: ModelRegistry,
        api_keys: dict[str, str],
        initial_model: str,
        session_store: SessionStore | None = None,
        session_id: str | None = None,
        initial_messages: list[ChatMessage] | None = None,
        total_prompt_tokens: int = 0,
        total_completion_tokens: int = 0,
        workspace_root: Path | None = None,
        auto_rag: bool = True,
        rag_store: PineconeRagStore | None = None,
        auto_approve_tools: bool | None = None,
        enable_tools: bool = True,
    ) -> None:
        self.config = config
        self.registry = registry
        self.api_keys = api_keys
        self.active_model = initial_model
        self.session_store = session_store
        self.session_id = session_id
        self.workspace_root = workspace_root or detect_workspace_root()
        self.auto_rag = auto_rag
        self.rag_store = rag_store
        self.enable_tools = enable_tools
        self.auto_approve_tools = (
            auto_approve_tools if auto_approve_tools is not None else (not sys.stdin.isatty())
        )
        self.toolset = AgentToolset(
            workspace_root=self.workspace_root,
            confirm_fn=self._confirm_tool_action,
            auto_approve=self.auto_approve_tools,
        )
        self.messages: list[ChatMessage] = (
            list(initial_messages)
            if initial_messages
            else [
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=build_system_prompt(config, self.workspace_root),
                )
            ]
        )
        self.total_prompt_tokens = total_prompt_tokens
        self.total_completion_tokens = total_completion_tokens
        self.last_suggested_model: str | None = None

    def _confirm_tool_action(self, action: str, target: str, preview: str | None) -> bool:
        """Interactive confirmation for local file writes, edits, and deletions."""
        if self.auto_approve_tools or not sys.stdin.isatty():
            return True

        console.print()
        print_info(f"Agent requests [bold]{action}[/bold] on [bold]{target}[/bold]")
        if preview:
            for line in preview.splitlines()[:8]:
                console.print(f"    [dim]{line}[/dim]")
        is_delete = action == "delete_file"
        default_choice = "n" if is_delete else "y"
        prompt_str = "  ▸ Allow? [y/N/a(always)]" if is_delete else "  ▸ Apply? [Y/n/a(always)]"
        ans = click.prompt(prompt_str, default=default_choice, show_default=False).strip().lower()
        if ans in ("a", "all", "always"):
            self.auto_approve_tools = True
            print_success("Auto-approve enabled for this chat session.")
            return True
        return ans in ("y", "yes")

    @property
    def provider_and_model(self) -> tuple[str, str]:
        """Split active_model ('provider/model') into (provider, model_id)."""
        if "/" not in self.active_model:
            return "", self.active_model
        provider_key, model_id = self.active_model.split("/", 1)
        return provider_key, model_id

    def get_budget(self, target_model: str | None = None) -> ContextBudget:
        """Compute current context budget against active or target model."""
        qid = target_model or self.active_model
        info = self.registry.get_model(qid)
        window = info.context_window if info else None
        used = estimate_messages_tokens(self.messages)
        return ContextBudget(
            used_tokens=used,
            context_window=window,
            total_prompt_tokens=self.total_prompt_tokens,
            total_completion_tokens=self.total_completion_tokens,
        )

    def clear_history(self) -> None:
        """Reset conversation turns while preserving the current session ID."""
        self.messages = [self.messages[0]]
        if self.session_store is not None and self.session_id is not None:
            self.session_store.replace_messages(self.session_id, self.messages)

    def start_new_session(self, *, title: str | None = None) -> SessionRecord | None:
        """Reset the context window and open a fresh session (preserving any prior session)."""
        sys_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content=build_system_prompt(self.config, self.workspace_root),
        )
        self.messages = [sys_msg]
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.last_suggested_model = None

        if self.session_store is not None:
            created = self.session_store.create_session(
                active_model=self.active_model,
                workspace_root=str(self.workspace_root),
                title=title,
                initial_messages=[sys_msg],
            )
            self.session_id = created.id
            return created

        self.session_id = None
        return None

    def compact_context(self, *, keep_last: int = 4) -> tuple[bool, int, int]:
        """
        Compact older turns into a concise summary message, preserving recent turns.

        Uses configured `summarization` model if available, falling back to deterministic
        extractive bullets when offline or unconfigured.
        """
        before_count = len(self.messages)
        system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        non_system = [m for m in self.messages if m.role != MessageRole.SYSTEM]
        if len(non_system) <= keep_last:
            return False, before_count, before_count

        older = non_system[:-keep_last] if keep_last > 0 else non_system
        summary_text = self._summarize_messages(older)

        tail = non_system[-keep_last:] if keep_last > 0 else []
        compacted_msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content=f"[Compacted conversation summary]\n{summary_text}",
        )
        self.messages = [*system_msgs[:1], compacted_msg, *tail]
        if self.session_store is not None and self.session_id is not None:
            self.session_store.replace_messages(self.session_id, self.messages)
        return True, before_count, len(self.messages)

    def _summarize_messages(self, older: list[ChatMessage]) -> str:
        """Summarize older messages via summarization model or extractive fallback."""
        target_model = self.config.models.summarization or self.active_model
        if "/" in target_model:
            pkey, mid = target_model.split("/", 1)
            api_key = self.api_keys.get(pkey)
            if api_key:
                transcript = "\n".join(f"{m.role.value}: {m.content[:500]}" for m in older)
                prompt = [
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content=(
                            "Summarize this conversation concisely, preserving key facts, "
                            "decisions, and file paths."
                        ),
                    ),
                    ChatMessage(role=MessageRole.USER, content=transcript),
                ]
                try:
                    chunks = asyncio.run(
                        self._collect_stream_text(
                            provider_key=pkey,
                            model_id=mid,
                            api_key=api_key,
                            messages=prompt,
                        )
                    )
                    if chunks.strip():
                        return chunks.strip()
                except ChatStreamError:
                    pass

        bullets: list[str] = []
        for msg in older:
            snippet = " ".join(msg.content.split())
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            bullets.append(f"- {msg.role.value}: {snippet}")
        return "\n".join(bullets)

    @staticmethod
    async def _collect_stream_text(
        *,
        provider_key: str,
        model_id: str,
        api_key: str,
        messages: list[ChatMessage],
    ) -> str:
        parts: list[str] = []
        async for chunk in stream_chat_completion(
            provider_key=provider_key,
            model_id=model_id,
            api_key=api_key,
            messages=messages,
            temperature=0.2,
        ):
            if chunk.delta:
                parts.append(chunk.delta)
        return "".join(parts)

    def switch_model(
        self,
        target_model: str,
        *,
        force_truncate: bool = False,
        persist_default: bool = False,
    ) -> tuple[bool, str]:
        """
        Switch the active session model per §4.3.

        Accepts <provider>/<model> or a unique bare model ID from the cached catalog.
        Never silently substitutes another model.
        """
        resolved_target = target_model.strip()
        if "/" not in resolved_target:
            if self.registry.models:
                current_provider, _ = self.provider_and_model
                found, suggestions = self.registry.resolve_model(
                    resolved_target,
                    preferred_provider=current_provider or None,
                )
                if found is not None:
                    resolved_target = found.qualified_id
                elif suggestions:
                    hint = ", ".join(m.qualified_id for m in suggestions[:3])
                    return (
                        False,
                        f"Multiple or partial matches for '{target_model}': {hint}",
                    )
                else:
                    return (
                        False,
                        "Use <provider>/<model_id> format (e.g. groq/llama-3.3-70b-versatile) "
                        "or '/model list <provider>' to browse.",
                    )
            else:
                return (
                    False,
                    "Use <provider>/<model_id> format (e.g. groq/llama-3.3-70b-versatile).",
                )

        provider_key, _ = resolved_target.split("/", 1)
        if provider_key not in PROVIDERS:
            return False, f"Unknown provider '{provider_key}'."
        if provider_key not in self.api_keys:
            return (
                False,
                f"No API key unlocked for '{provider_key}'. "
                f"Add it with 'valkyrie keys add {provider_key}'.",
            )

        info = self.registry.get_model(resolved_target)
        if self.registry.models and info is None:
            return (
                False,
                f"Model '{resolved_target}' was not found in your catalog. "
                "Run '/model list' to inspect compatible choices.",
            )
        if info is not None and not info.is_active:
            return False, f"Model '{resolved_target}' is marked inactive/retired."

        target_window = info.context_window if info else None
        budget = self.get_budget(resolved_target)
        if not budget.fits(target_window):
            if not force_truncate:
                return (
                    False,
                    f"Current context (~{budget.used_tokens:,} tokens) exceeds "
                    f"'{resolved_target}' window ({target_window:,} tokens). "
                    "Clear or compact history before switching.",
                )
            self.clear_history()

        self.active_model = resolved_target
        self.last_suggested_model = None
        if self.session_store is not None and self.session_id is not None:
            self.session_store.update_active_model(self.session_id, resolved_target)
        if persist_default:
            self.config.models.chat = resolved_target
            self.config.save()
        return True, f"Switched active model -> {resolved_target}."

    def _build_turn_context(self, user_text: str) -> ChatMessage | None:
        """Collect @path file attachments and optional Pinecone RAG context for a turn."""
        sections: list[str] = []

        # 1. Read-only @path attachments inside workspace scope
        seen: set[str] = set()
        for raw_path in _AT_PATH_RE.findall(user_text):
            if raw_path in seen:
                continue
            seen.add(raw_path)
            try:
                res = read_workspace_file(self.workspace_root, raw_path)
                render_tool_card(
                    tool="read",
                    status="ok",
                    target=res.rel_path,
                    summary=f"L{res.start_line}-L{res.end_line} of {res.total_lines} lines",
                )
                sections.append(
                    f"[File: {res.rel_path} L{res.start_line}-L{res.end_line}]\n{res.content}"
                )
            except PermissionError as exc:
                render_tool_card(tool="read", status="blocked", target=raw_path, summary=str(exc))
            except (FileNotFoundError, ValueError):
                pass

        # 2. Automatic Pinecone retrieval context injection when configured
        pc_key = resolve_pinecone_api_key(self.workspace_root, self.api_keys)
        if self.auto_rag and (pc_key or self.rag_store is not None):
            try:
                hits, _ = search_workspace_rag(
                    user_text,
                    self.workspace_root,
                    config=self.config,
                    api_keys=self.api_keys,
                    pinecone_api_key=pc_key,
                    store=self.rag_store,
                    top_k=3,
                )
                relevant = [h for h in hits if h.score >= 0.25]
                if relevant:
                    cites = ", ".join(h.citation for h in relevant)
                    render_tool_card(
                        tool="rag",
                        status="ok",
                        target=f"{len(relevant)} Pinecone chunk(s)",
                        summary=f"Citations: {cites}",
                    )
                    sections.append(format_rag_context(relevant))
            except Exception as exc:
                print_warning(f"Pinecone retrieval unavailable: {exc}")

        if not sections:
            return None
        return ChatMessage(role=MessageRole.SYSTEM, content="\n\n".join(sections))

    def _handle_stream_error(self, exc: ChatStreamError, provider_key: str) -> None:
        """Render clean diagnostics and deprecated/404 model replacement hints."""
        self.last_suggested_model = None
        err_str = str(exc)
        is_missing_or_retired = (
            exc.status_code == 404
            or "no longer available" in err_str.lower()
            or "deprecated" in err_str.lower()
            or "not found" in err_str.lower()
        )

        details: str | None = None
        if is_missing_or_retired:
            failing_info = self.registry.get_model(self.active_model)
            if failing_info is not None:
                failing_info.is_active = False

            alternatives: list[str] = []
            if exc.suggested_model and exc.suggested_model != self.active_model:
                alternatives.append(exc.suggested_model)

            for m in self.registry.list_models(provider=provider_key, role="chat"):
                if (
                    m.is_active
                    and m.qualified_id != self.active_model
                    and m.qualified_id not in alternatives
                ):
                    alternatives.append(m.qualified_id)
                if len(alternatives) >= 4:
                    break

            if not alternatives:
                for pkey in self.api_keys:
                    for m in self.registry.list_models(provider=pkey, role="chat"):
                        if m.is_active and m.qualified_id != self.active_model:
                            alternatives.append(m.qualified_id)
                            break

            if alternatives:
                self.last_suggested_model = alternatives[0]
                alt_lines = "\n".join(f"  ▸ /model {alt}" for alt in alternatives)
                details = f"Switch immediately with:\n{alt_lines}\n  ▸ /model pick {provider_key}"

        render_tool_card(
            tool="provider",
            status="error",
            target=self.active_model,
            summary=err_str,
            details=details,
        )

    async def send_turn(self, user_text: str) -> str | None:
        """Append user message, run agentic tool-calling loop, and update accounting."""
        provider_key, model_id = self.provider_and_model
        api_key = self.api_keys.get(provider_key)
        if not api_key:
            print_error(
                f"No API key available for provider '{provider_key}'. "
                f"Cannot invoke '{self.active_model}'."
            )
            return None

        extra_ctx = self._build_turn_context(user_text)
        if extra_ctx is not None:
            print_info(
                f"Workspace context attached -> hosted request to [bold]{provider_key}[/bold]."
            )
        user_msg = ChatMessage(role=MessageRole.USER, content=user_text)
        self.messages.append(user_msg)

        tools_enabled = self.enable_tools
        final_reply: str | None = None
        user_persisted = False

        for step in range(_MAX_TOOL_STEPS):
            # Insert ephemeral extra_ctx just before the user message on step 0
            if extra_ctx is not None and step == 0:
                request_messages = [*self.messages[:-1], extra_ctx, user_msg]
            else:
                request_messages = self.messages

            openai_tools = self.toolset.openai_tools() if tools_enabled else None
            gemini_decls = self.toolset.gemini_declarations() if tools_enabled else None

            try:
                chunks = stream_chat_completion(
                    provider_key=provider_key,
                    model_id=model_id,
                    api_key=api_key,
                    messages=request_messages,
                    openai_tools=openai_tools,
                    gemini_declarations=gemini_decls,
                )
                reply_text, usage, tool_calls = await render_agent_stream(
                    chunks,
                    qualified_model=self.active_model,
                    prompt_messages=request_messages,
                )
            except ChatStreamError as exc:
                err_lower = str(exc).lower()
                if (
                    tools_enabled
                    and exc.status_code == 400
                    and any(k in err_lower for k in ("tool", "function"))
                ):
                    tools_enabled = False
                    continue
                if step == 0:
                    self.messages.pop()
                self._handle_stream_error(exc, provider_key)
                return None

            self.last_suggested_model = None
            self.total_prompt_tokens += usage.prompt_tokens
            self.total_completion_tokens += usage.completion_tokens

            if (
                not user_persisted
                and self.session_store is not None
                and self.session_id is not None
            ):
                self.session_store.append_message(self.session_id, user_msg)
                self.session_store.auto_title_if_default(self.session_id, user_text)
                user_persisted = True

            assistant_msg = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=reply_text,
                model=self.active_model,
                tool_calls=[tc.to_openai_dict() for tc in tool_calls] if tool_calls else None,
                usage=usage,
            )
            self.messages.append(assistant_msg)
            if self.session_store is not None and self.session_id is not None:
                self.session_store.append_message(self.session_id, assistant_msg)

            if not tool_calls:
                final_reply = reply_text
                break

            # Execute requested LangChain tools and feed results back
            for tc in tool_calls:
                _, output = self.toolset.execute(tc.name, tc.arguments)
                tool_msg = ChatMessage(
                    role=MessageRole.TOOL,
                    name=tc.name,
                    tool_call_id=tc.id,
                    content=output,
                )
                self.messages.append(tool_msg)
                if self.session_store is not None and self.session_id is not None:
                    self.session_store.append_message(self.session_id, tool_msg)

        return final_reply


def build_command_registry(engine: ChatEngine) -> SlashCommandRegistry:
    """Build the slash command registry for an interactive ChatEngine."""
    reg = SlashCommandRegistry(feature_flags=engine.config.feature_flags)

    def cmd_help(_args: list[str]) -> bool:
        console.print()
        print_rule("Chat Commands")
        for c in reg.help_commands():
            alias_str = f" [dim]({', '.join(c.aliases)})[/dim]" if c.aliases else ""
            label = f"{c.usage}{alias_str}"
            if c.upcoming:
                label += " [dim](upcoming)[/dim]"
            print_kv(label, c.description)
        console.print()
        return True

    def cmd_model(args: list[str]) -> bool:
        _handle_model_slash(args, engine)
        return True

    def cmd_budget(_args: list[str]) -> bool:
        budget = engine.get_budget()
        console.print()
        print_kv("Model", f"[model]{engine.active_model}[/model]")
        print_kv("Context", budget.format_summary())
        print_kv(
            "Session totals",
            f"{budget.total_prompt_tokens:,} in · {budget.total_completion_tokens:,} out",
        )
        console.print()
        return True

    def cmd_clear(_args: list[str]) -> bool:
        engine.clear_history()
        console.clear()
        print_success("Conversation context cleared (session preserved).")
        console.print()
        return True

    def cmd_new(args: list[str]) -> bool:
        title = " ".join(args).strip() or None
        created = engine.start_new_session(title=title)
        console.clear()
        _render_chat_hud(engine)
        if created is not None:
            print_success(
                f"Started new session [bold]{created.title}[/bold] ([dim]{created.id}[/dim])."
            )
        else:
            print_success("Started new chat context window (ephemeral session).")
        console.print()
        return True

    def cmd_compact(args: list[str]) -> bool:
        keep = int(args[0]) if args and args[0].isdigit() else 4
        ok, before_cnt, after_cnt = engine.compact_context(keep_last=keep)
        console.print()
        if ok:
            print_success(f"Compacted context: {before_cnt} -> {after_cnt} messages.")
            print_kv("Budget", engine.get_budget().format_summary())
        else:
            print_warning("Not enough messages to compact.")
        console.print()
        return True

    def cmd_session(_args: list[str]) -> bool:
        console.print()
        print_rule("Current Session")
        print_kv("ID", engine.session_id or "[muted]ephemeral[/muted]")
        if engine.session_store and engine.session_id:
            sess = engine.session_store.get_session(engine.session_id)
            if sess:
                print_kv("Title", sess.title)
                print_kv("Messages", str(sess.message_count))
                if sess.last_checkpoint_id:
                    print_kv("Checkpoint", sess.last_checkpoint_id)
        print_kv("Model", f"[model]{engine.active_model}[/model]")
        console.print()
        return True

    def cmd_workspace(_args: list[str]) -> bool:
        files = list_workspace_files(engine.workspace_root)
        console.print()
        print_rule("Workspace")
        print_kv("Root", str(engine.workspace_root))
        print_kv("Accessible", f"{len(files)} files (use @ to attach)")
        console.print()
        return True

    def cmd_read(args: list[str]) -> bool:
        if not args:
            print_info("Usage: /read <path> [start_line] [end_line]")
            return True
        raw_path = args[0]
        start_line = int(args[1]) if len(args) >= 2 and args[1].isdigit() else 1
        end_line = int(args[2]) if len(args) >= 3 and args[2].isdigit() else None
        try:
            res = read_workspace_file(
                engine.workspace_root,
                raw_path,
                start_line=start_line,
                end_line=end_line,
            )
            preview_lines = res.content.splitlines()[:12]
            preview = "\n".join(preview_lines)
            if len(res.content.splitlines()) > 12:
                preview += "\n..."
            render_tool_card(
                tool="read",
                status="ok",
                target=res.rel_path,
                summary=f"Read L{res.start_line}-L{res.end_line} of {res.total_lines} lines",
                details=preview,
            )
        except PermissionError as exc:
            render_tool_card(tool="read", status="blocked", target=raw_path, summary=str(exc))
        except (FileNotFoundError, ValueError) as exc:
            render_tool_card(tool="read", status="error", target=raw_path, summary=str(exc))
        return True

    def cmd_index(args: list[str]) -> bool:
        target = args[0] if args else "."
        pc_key = resolve_pinecone_api_key(engine.workspace_root, engine.api_keys)
        print_info(
            f"Data transfer: indexing '{target}' -> Pinecone DB "
            f"'{engine.config.pinecone.index_name}' (zero local storage)"
        )
        try:
            summary = index_workspace_path(
                engine.workspace_root,
                target,
                config=engine.config,
                api_keys=engine.api_keys,
                pinecone_api_key=pc_key,
                store=engine.rag_store,
            )
            render_tool_card(
                tool="index",
                status="ok",
                target=target,
                summary=(
                    f"{summary.files_indexed} files, {summary.chunks_upserted} chunks -> "
                    f"{summary.index_name} [{summary.namespace}] ({summary.embedding_backend})"
                ),
            )
        except Exception as exc:
            render_tool_card(tool="index", status="error", target=target, summary=str(exc))
        return True

    def cmd_search(args: list[str]) -> bool:
        if not args:
            print_info("Usage: /search <query>")
            return True
        query = " ".join(args)
        pc_key = resolve_pinecone_api_key(engine.workspace_root, engine.api_keys)
        try:
            hits, backend = search_workspace_rag(
                query,
                engine.workspace_root,
                config=engine.config,
                api_keys=engine.api_keys,
                pinecone_api_key=pc_key,
                store=engine.rag_store,
            )
            if not hits:
                print_info("No matching chunks found in Pinecone namespace.")
                return True
            lines = [f"▸ {h.citation} ({h.score:.3f})" for h in hits]
            render_tool_card(
                tool="search",
                status="ok",
                target=query,
                summary=f"{len(hits)} Pinecone hit(s) via {backend}",
                details="\n".join(lines),
            )
        except Exception as exc:
            render_tool_card(tool="search", status="error", target=query, summary=str(exc))
        return True

    def cmd_rag(args: list[str]) -> bool:
        if args and args[0].lower() in ("on", "off"):
            engine.auto_rag = args[0].lower() == "on"
            state = "enabled" if engine.auto_rag else "disabled"
            print_success(f"Auto-RAG Pinecone injection {state}.")
            return True
        pc_key = resolve_pinecone_api_key(engine.workspace_root, engine.api_keys)
        console.print()
        print_kv("Auto-RAG", "on" if engine.auto_rag else "off")
        print_kv("Storage", "Pinecone DB only (app .env configured)")
        print_kv("Pinecone index", engine.config.pinecone.index_name)
        print_kv(
            "Pinecone backend",
            "connected" if (pc_key or engine.rag_store) else "missing in .env",
        )
        console.print()
        return True

    def cmd_web(args: list[str]) -> bool:
        if not args:
            print_info("Usage: /web <search query>")
            return True
        query = " ".join(args)
        try:
            hits = run_duckduckgo_search(query, max_results=5)
            if not hits:
                print_warning(f"No DuckDuckGo results for '{query}'.")
                return True
            lines = [
                f"▸ [bold]{h['title']}[/bold]\n  [dim]{h['link']}[/dim]\n  {h['snippet'][:140]}"
                for h in hits
            ]
            render_tool_card(
                tool="web",
                status="ok",
                target=query,
                summary=f"{len(hits)} DuckDuckGo result(s) via LangChain",
                details="\n".join(lines[:3]),
            )
        except Exception as exc:
            render_tool_card(tool="web", status="error", target=query, summary=str(exc))
        return True

    def cmd_auto(args: list[str]) -> bool:
        if args and args[0].lower() in ("on", "off"):
            engine.auto_approve_tools = args[0].lower() == "on"
        else:
            engine.auto_approve_tools = not engine.auto_approve_tools
        # Propagate to run_command / pkg_install tools
        engine.toolset.set_auto_approve(engine.auto_approve_tools)
        state = (
            "ON (no confirmation prompts)"
            if engine.auto_approve_tools
            else "OFF (prompt before file changes)"
        )
        print_success(f"Tool auto-approve: {state}")
        return True

    def cmd_account(args: list[str]) -> bool:
        _handle_account_slash(args)
        return True

    def cmd_exit(_args: list[str]) -> bool:
        print_info("Session closed.")
        return False

    reg.register(
        SlashCommand("/help", "/help", "List available commands", cmd_help, aliases=("/h", "/?"))
    )
    reg.register(
        SlashCommand(
            "/model",
            "/model [<provider>|ls|pick|rf|<id>]",
            "Inspect, filter by provider, or switch models anytime",
            cmd_model,
            aliases=("/m",),
        )
    )
    reg.register(
        SlashCommand(
            "/budget",
            "/budget",
            "Show context window accounting",
            cmd_budget,
            aliases=("/b",),
        )
    )
    reg.register(
        SlashCommand(
            "/compact",
            "/compact [keep]",
            "Summarize older turns and trim context window",
            cmd_compact,
            aliases=("/cmp",),
        )
    )
    reg.register(
        SlashCommand(
            "/new",
            "/new [title]",
            "Create a new chat session with a fresh context window",
            cmd_new,
            aliases=("/n",),
        )
    )
    reg.register(
        SlashCommand(
            "/clear",
            "/clear",
            "Clear screen and reset conversation context",
            cmd_clear,
            aliases=("/c", "/cls"),
        )
    )
    reg.register(
        SlashCommand(
            "/session",
            "/session",
            "Show active session metadata",
            cmd_session,
            aliases=("/ss",),
        )
    )
    reg.register(
        SlashCommand(
            "/workspace",
            "/workspace",
            "Show workspace root and file count",
            cmd_workspace,
            aliases=("/ws",),
        )
    )
    reg.register(
        SlashCommand(
            "/read",
            "/read <path> [start] [end]",
            "Read a file inside workspace scope",
            cmd_read,
            aliases=("/r",),
        )
    )
    reg.register(
        SlashCommand(
            "/index",
            "/index [path]",
            "Index workspace files into Pinecone DB",
            cmd_index,
            aliases=("/i",),
        )
    )
    reg.register(
        SlashCommand(
            "/search",
            "/search <query>",
            "Search Pinecone workspace index with citations",
            cmd_search,
            aliases=("/s",),
        )
    )
    reg.register(
        SlashCommand(
            "/rag",
            "/rag [on|off|status]",
            "Configure automatic Pinecone RAG context injection",
            cmd_rag,
        )
    )
    reg.register(
        SlashCommand(
            "/web",
            "/web <query>",
            "Search the live web with DuckDuckGo via LangChain",
            cmd_web,
            aliases=("/w",),
        )
    )
    reg.register(
        SlashCommand(
            "/auto",
            "/auto [on|off]",
            "Toggle auto-approval for local file write/edit/delete",
            cmd_auto,
            aliases=("/a",),
        )
    )
    reg.register(
        SlashCommand(
            "/account",
            "/account [st|sw|del|in|out]",
            "Inspect, switch, or delete your signed-in account",
            cmd_account,
            aliases=("/acc", "/auth"),
        )
    )
    reg.register(
        SlashCommand("/exit", "/exit", "Exit chat", cmd_exit, aliases=("/q", "/quit"))
    )

    # ── /run  ────────────────────────────────────────────────────────────────

    def cmd_run(args: list[str]) -> bool:
        """Execute a raw shell command inside the workspace."""
        from valkyrie.tools.run_command import run_shell_command

        if not args:
            print_info("Usage: /run <shell command>")
            return True
        cmd = " ".join(args)
        try:
            output = run_shell_command(
                cmd,
                workspace_root=engine.workspace_root,
                confirm_fn=engine._confirm_tool_action,
                auto_approve=engine.auto_approve_tools,
            )
            console.print(output)
        except (PermissionError, RuntimeError, ValueError) as exc:
            render_tool_card(tool="run", status="error", target=cmd, summary=str(exc))
        return True

    reg.register(
        SlashCommand(
            "/run",
            "/run <command>",
            "Execute a shell command inside the workspace",
            cmd_run,
        )
    )

    # ── /pkg  ────────────────────────────────────────────────────────────────

    def cmd_pkg(args: list[str]) -> bool:
        """Install / manage packages via pip, npm, brew, cargo, apt, etc."""
        from valkyrie.tools.pkg_manager import _KNOWN_MANAGERS, run_pkg_command

        # /pkg [manager] [action] [packages…]
        # /pkg install <name>          → auto-detect manager
        # /pkg pip install requests
        if not args:
            print_info(
                "Usage: /pkg [manager] <action> [packages…]\n"
                f"Managers: {', '.join(sorted(_KNOWN_MANAGERS))}\n"
                "Example:  /pkg pip install httpx\n"
                "          /pkg npm install lodash\n"
                "          /pkg install requests  (auto-detects pip)"
            )
            return True

        # If first arg is a known manager, use it; otherwise default to pip
        if args[0].lower() in _KNOWN_MANAGERS:
            manager = args[0].lower()
            rest = args[1:]
        else:
            manager = "pip"
            rest = args

        if not rest:
            print_info(f"Usage: /pkg {manager} <action> [packages…]")
            return True

        action = rest[0].lower()
        packages = rest[1:]

        output = run_pkg_command(
            manager,
            action,
            packages,
            workspace_root=engine.workspace_root,
            confirm_fn=engine._confirm_tool_action,
            auto_approve=engine.auto_approve_tools,
        )
        if output:
            console.print(output)
        return True

    reg.register(
        SlashCommand(
            "/pkg",
            "/pkg [manager] <action> [packages…]",
            "Install, uninstall, or list packages (pip, npm, brew, cargo, apt …)",
            cmd_pkg,
        )
    )

    # Upcoming Beta capabilities — hidden from normal help, non-executable
    reg.register(
        SlashCommand(
            "/plan",
            "/plan <goal>",
            "Create a step-by-step execution plan before editing",
            upcoming=True,
        )
    )
    return reg


def _handle_slash_command(
    raw: str,
    engine: ChatEngine,
    registry: SlashCommandRegistry | None = None,
) -> bool:
    """
    Handle an in-chat slash command.

    Returns False if the REPL should exit, True otherwise.
    """
    reg = registry or build_command_registry(engine)
    parts = raw.strip().split()
    cmd_name = parts[0].lower()

    if cmd_name == "/":
        for c in reg.executable_commands():
            print_kv(c.usage, c.description)
        return True

    cmd = reg.resolve(cmd_name)
    if cmd is not None and cmd.handler is not None:
        return cmd.handler(parts[1:])

    matches = reg.filter_prefix(cmd_name)
    if matches:
        names = ", ".join(m.name for m in matches)
        print_warning(f"Ambiguous or partial command '{cmd_name}'. Matches: {names}")
    else:
        print_warning(f"Unknown command '{cmd_name}'. Type /help to list commands.")
    return True


def _render_provider_pills(engine: ChatEngine, active_provider: str | None) -> None:
    """Render provider filter pills inside chat."""
    counts = engine.registry.provider_counts()
    total = sum(counts.values())
    bar = Text("  FILTER  ", style="grey62")
    if active_provider is None:
        bar.append(f" ALL ({total}) ", style="bold black on bright_cyan")
    else:
        bar.append(f"ALL ({total})", style="grey62")

    for pkey in PROVIDERS:
        cnt = counts.get(pkey, 0)
        bar.append("  ·  ", style="grey35")
        if active_provider == pkey:
            bar.append(f" {pkey.upper()} ({cnt}) ", style="bold black on bright_cyan")
        elif cnt > 0:
            unlocked = "✓" if pkey in engine.api_keys else "locked"
            bar.append(f"{pkey} ({cnt})", style="bright_white")
            if unlocked == "locked":
                bar.append(" [locked]", style="grey42")
        else:
            bar.append(f"{pkey} (0)", style="grey42")
    console.print(bar)


def _render_model_table(
    models: list[ModelInfo],
    *,
    engine: ChatEngine,
    provider_filter: str | None,
) -> None:
    """Display filtered models in a compact editorial Rich table."""
    console.print()
    _render_provider_pills(engine, provider_filter)
    console.print()

    if not models:
        print_warning("No models match your filter.")
        console.print()
        return

    table = Table(
        box=box.ROUNDED,
        border_style="rule",
        header_style="bold bright_white",
        show_lines=False,
        pad_edge=True,
    )
    table.add_column("#", style="grey50", justify="right", width=3)
    table.add_column("Model", style="model")
    table.add_column("Caps", style="bright_cyan")
    table.add_column("Ctx", justify="right", style="dim")
    table.add_column("State", justify="right")

    for idx, m in enumerate(models, start=1):
        caps = " · ".join(c.value for c in m.capabilities)
        ctx = (
            f"{m.context_window / 1_000_000:.1f}M"
            if m.context_window and m.context_window >= 1_000_000
            else (f"{m.context_window // 1000}k" if m.context_window else "?")
        )
        if m.qualified_id == engine.active_model:
            state = "[tag] ACTIVE [/tag]"
        elif not m.is_active:
            state = "[warning]retired[/warning]"
        elif m.provider not in engine.api_keys:
            state = "[muted]no key[/muted]"
        else:
            state = "[success]ready[/success]"
        table.add_row(str(idx), m.qualified_id, caps, ctx, state)

    console.print(table)
    console.print(
        "  [muted]Switch: [bold]/model <provider/id>[/bold] · "
        "Filter: [bold]/model <groq|gemini|nvidia>[/bold] · "
        "Pick: [bold]/model pick[/bold][/muted]"
    )
    console.print()


def _attempt_model_switch(engine: ChatEngine, target: str) -> None:
    """Attempt model switch, offering truncate confirmation if context exceeds window."""
    ok, msg = engine.switch_model(target)
    if ok:
        print_success(msg)
        return

    if "exceeds" in msg:
        print_warning(msg)
        if click.confirm("  Clear conversation context and switch anyway?", default=False):
            ok2, msg2 = engine.switch_model(target, force_truncate=True)
            if ok2:
                print_success(msg2)
            else:
                print_error(msg2)
        return

    print_error(msg)


def _interactive_model_picker(engine: ChatEngine, provider_filter: str | None = None) -> None:
    """Interactive provider-filterable numbered selector inside chat."""
    current_filter = provider_filter.lower() if provider_filter else None
    while True:
        candidates = [
            m
            for m in engine.registry.list_models(provider=current_filter, role="chat")
            if m.is_active
        ]
        if not candidates:
            print_warning("No active chat models available for this filter.")
            return

        shown = candidates[:15]
        _render_model_table(shown, engine=engine, provider_filter=current_filter)
        if len(candidates) > len(shown):
            print_info(
                f"Showing top {len(shown)} of {len(candidates)} models. "
                "Type a provider name (groq/gemini/nvidia) or 'all' to filter."
            )
        raw = click.prompt(
            "  Pick # (or provider name, or 'q' to cancel)",
            default="q",
        ).strip()
        lower = raw.lower()
        if lower in ("q", "quit", "cancel", ""):
            print_info("Model kept unchanged.")
            return
        if lower == "all":
            current_filter = None
            continue
        if lower in PROVIDERS:
            current_filter = lower
            continue
        if raw.isdigit():
            pos = int(raw) - 1
            if 0 <= pos < len(shown):
                _attempt_model_switch(engine, shown[pos].qualified_id)
                return
        _attempt_model_switch(engine, raw)
        return


def _handle_model_slash(args: list[str], engine: ChatEngine) -> None:
    """
    Handle /model commands in chat:
      /model                        -> active model & role matrix
      /model <provider> [search]    -> filter catalog by provider
      /model list [provider] [q]    -> list full/filtered catalog
      /model filter <provider> [q]  -> filter catalog by provider
      /model pick [provider]        -> interactive numbered switcher
      /model refresh [provider]     -> fetch live models from unlocked providers
      /model [use] <model_id>       -> switch active model immediately
    """
    if not args:
        console.print()
        print_rule("Session Model")
        budget = engine.get_budget()
        print_kv("active", f"[model]{engine.active_model}[/model]")
        print_kv("budget", budget.format_summary())
        console.print()
        for role in ("chat", "code", "planner", "vision", "summarization", "embeddings"):
            val = getattr(engine.config.models, role, None)
            print_kv(role, val or "[muted]unassigned[/muted]")
        console.print()
        _render_provider_pills(engine, None)
        console.print(
            "  [muted]Commands: [bold]/model <provider>[/bold] · "
            "[bold]/model pick[/bold] · [bold]/model <id>[/bold] · "
            "[bold]/model refresh[/bold][/muted]"
        )
        console.print()
        return

    sub_aliases = {
        "ls": "list",
        "f": "filter",
        "p": "pick",
        "rf": "refresh",
        "u": "use",
    }
    sub = sub_aliases.get(args[0].lower(), args[0].lower())

    if sub == "refresh":
        target_p = args[1].lower() if len(args) >= 2 and args[1].lower() in PROVIDERS else None
        keys = (
            {target_p: engine.api_keys[target_p]}
            if target_p and target_p in engine.api_keys
            else dict(engine.api_keys)
        )
        if not keys:
            print_error("No matching unlocked API keys in this session.")
            return
        print_info(f"Refreshing live catalogs for: {', '.join(keys.keys())}…")
        summary = asyncio.run(engine.registry.refresh(keys))
        for pkey, (valid, cnt) in summary.items():
            if valid:
                print_success(f"{pkey:<10} {cnt} models synced")
            else:
                print_warning(f"{pkey:<10} refresh failed")
        return

    if sub in ("pick", "switch"):
        p_filter = args[1].lower() if len(args) >= 2 and args[1].lower() in PROVIDERS else None
        _interactive_model_picker(engine, p_filter)
        return

    if sub in ("list", "filter") or sub in PROVIDERS:
        if not engine.registry.models:
            console.print()
            print_info("No cached models. Run '/model refresh' or 'valkyrie model refresh'.")
            console.print()
            return

        rest = args if sub in PROVIDERS else args[1:]
        provider_filter: str | None = None
        search_terms: list[str] = []
        for token in rest:
            tok_lower = token.lower()
            if tok_lower in PROVIDERS and provider_filter is None:
                provider_filter = tok_lower
            elif tok_lower not in ("all", "*"):
                search_terms.append(token)

        search_q = " ".join(search_terms) if search_terms else None
        models = engine.registry.list_models(provider=provider_filter, search=search_q)
        _render_model_table(models, engine=engine, provider_filter=provider_filter)
        return

    if sub == "use":
        if len(args) < 2:
            print_info("Usage: /model use <provider/model_id>")
            return
        _attempt_model_switch(engine, args[1])
        return

    # Shorthand: `/model <provider/model_id>` or `/model <bare_model_id>`
    _attempt_model_switch(engine, args[0])


def _handle_account_slash(args: list[str]) -> None:
    """
    Handle /account (and /auth) commands in chat:
      /account [status]    -> inspect current signed-in account
      /account login       -> sign in with Google via browser
      /account switch      -> switch Google account via browser account picker
      /account delete      -> delete signed-in Firebase account & remote vault
      /account logout      -> sign out locally
    """
    from valkyrie.auth.account import (
        delete_account,
        login_account,
        logout_account,
        show_account_status,
        switch_account,
    )

    sub_aliases = {
        "s": "status",
        "st": "status",
        "sw": "switch",
        "del": "delete",
        "rm": "delete",
        "in": "login",
        "out": "logout",
    }
    raw_sub = args[0].lower() if args else "status"
    sub = sub_aliases.get(raw_sub, raw_sub)
    if sub == "status":
        show_account_status()
        console.print(
            "  [muted]Commands: [bold]/account switch[/bold] · "
            "[bold]/account delete[/bold] · [bold]/account login[/bold] · "
            "[bold]/account logout[/bold][/muted]"
        )
        console.print()
        return

    if sub == "login":
        login_account(select_account=False)
        return

    if sub == "switch":
        switch_account(interactive=True)
        return

    if sub == "delete":
        assume_yes = "--yes" in args[1:]
        purge_local = "--purge-local" in args[1:]
        delete_account(assume_yes=assume_yes, purge_local=purge_local)
        return

    if sub == "logout":
        logout_account()
        return

    print_warning(
        f"Unknown /account action '{sub}'. "
        "Use: status, switch, delete, login, or logout."
    )


def _render_chat_hud(engine: ChatEngine) -> None:
    """Render the responsive startup HUD card for Valkyrie Chat."""
    budget = engine.get_budget()
    ratio = (budget.used_tokens / budget.context_window) if budget.context_window else 0.0
    pc_key = resolve_pinecone_api_key(engine.workspace_root, engine.api_keys)
    rag_label = (
        f"[success]Pinecone · {engine.config.pinecone.index_name}[/success]"
        if (pc_key or engine.rag_store)
        else "[warning]Pinecone unconfigured[/warning]"
    )

    grid = Table.grid(expand=True, padding=(0, 2))
    if console.width >= 76:
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        left = Text.from_markup(
            f"[muted]MODEL[/muted]      [model]{engine.active_model}[/model]\n"
            f"[muted]SESSION[/muted]    [dim]{engine.session_id or 'ephemeral'}[/dim]\n"
            f"[muted]WORKSPACE[/muted]  [dim]{engine.workspace_root.name}[/dim]"
        )
        pct = f"{ratio * 100:.0f}%" if budget.context_window else "—"
        right = Text.from_markup(
            f"[muted]CONTEXT[/muted]    {render_meter(ratio)} [dim]{pct}[/dim]\n"
            f"[muted]VECTOR DB[/muted]  {rag_label}\n"
            f"[muted]SHORTCUTS[/muted]  [accent]/new[/accent] · [accent]/model[/accent] · "
            f"[accent]/account[/accent] · [accent]@file[/accent] · [accent]/exit[/accent]"
        )
        grid.add_row(left, right)
    else:
        grid.add_column()
        grid.add_row(
            Text.from_markup(
                f"[muted]MODEL[/muted]   [model]{engine.active_model}[/model]\n"
                f"[muted]BUDGET[/muted]  {budget.format_summary()}\n"
                f"[muted]RAG[/muted]     {rag_label}\n"
                f"[muted]CMDS[/muted]    /model · @file · /help"
            )
        )

    console.print()
    console.print(
        Panel(
            grid,
            box=box.ROUNDED,
            title="[heading]◆ VALKYRIE CHAT[/heading]",
            title_align="left",
            border_style="bright_cyan",
            padding=(0, 1),
        )
    )
    console.print()


def _build_toolbar(engine: ChatEngine) -> HTML:
    """Build live bottom toolbar HTML for prompt_toolkit."""
    budget = engine.get_budget()
    if budget.context_window:
        pct = int((budget.used_tokens / budget.context_window) * 100)
        ctx_str = f"ctx {pct}%"
    else:
        ctx_str = f"ctx ~{budget.used_tokens:,}"

    rag_state = "pinecone:on" if engine.auto_rag else "pinecone:off"
    return HTML(
        f" <b>◆ {engine.active_model}</b> │ {ctx_str} │ {rag_state} "
        f"│ <i>/new  /model  /web  /auto  @file  /help</i> "
    )


def run_chat_repl(engine: ChatEngine) -> None:
    """Run the interactive terminal chat loop."""
    registry = build_command_registry(engine)
    completer = ValkyrieCompleter(registry, engine.workspace_root, model_registry=engine.registry)
    session: PromptSession[str] = PromptSession(
        completer=completer,
        complete_while_typing=True,
        style=_PROMPT_STYLE,
        bottom_toolbar=lambda: _build_toolbar(engine),
    )

    _render_chat_hud(engine)

    interrupt_pending = False
    while True:
        try:
            provider, _, model_short = engine.active_model.partition("/")
            badge = f"{provider}/{model_short}" if model_short else engine.active_model
            prompt_text = HTML(
                f"<ansibrightcyan>◆ valkyrie</ansibrightcyan> "
                f"<ansibrightmagenta>[{badge}]</ansibrightmagenta> "
                f"<b>›</b> "
            )
            user_input = session.prompt(prompt_text)
            interrupt_pending = False
        except KeyboardInterrupt:
            if interrupt_pending:
                console.print()
                print_info("Session closed.")
                break
            interrupt_pending = True
            console.print("  [dim](Press Ctrl+C again, Ctrl+D, or /exit to quit.)[/dim]")
            continue
        except EOFError:
            console.print()
            print_info("Session closed.")
            break

        stripped = user_input.strip()
        if not stripped:
            continue

        if stripped.startswith("/"):
            if not _handle_slash_command(stripped, engine, registry):
                break
            continue

        asyncio.run(engine.send_turn(stripped))

        # Instant 1-key recovery when a model returns 404 / deprecated
        if engine.last_suggested_model and sys.stdin.isatty():
            suggested = engine.last_suggested_model
            engine.last_suggested_model = None
            if click.confirm(f"  ▸ Switch active model to {suggested} now?", default=True):
                _attempt_model_switch(engine, suggested)

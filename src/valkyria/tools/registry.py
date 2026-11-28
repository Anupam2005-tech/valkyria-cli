"""
Agent toolset — LangChain tools, risk-tier classification, schema export, and execution.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain_core.utils.function_calling import convert_to_openai_tool

from valkyria.core.cards import render_tool_card
from valkyria.tools.local_fs import ConfirmCallback, make_local_tools
from valkyria.tools.pkg_manager import make_pkg_tool
from valkyria.tools.run_command import make_run_command_tool
from valkyria.tools.web_search import make_web_search_tool

if TYPE_CHECKING:
    from pathlib import Path

    from langchain_core.tools import BaseTool

READ_ONLY_TOOLS = frozenset({"read_file", "list_directory", "search_files", "web_search"})
MUTATING_TOOLS = frozenset({"write_file", "edit_file", "delete_file", "run_command", "pkg_install"})


def _sanitize_gemini_schema(node: Any) -> Any:
    """Strip JSON Schema keys rejected by Gemini v1beta functionDeclarations."""
    if isinstance(node, dict):
        cleaned: dict[str, Any] = {}
        for k, v in node.items():
            if k in ("title", "default", "additionalProperties", "$schema"):
                continue
            cleaned[k] = _sanitize_gemini_schema(v)
        return cleaned
    if isinstance(node, list):
        return [_sanitize_gemini_schema(item) for item in node]
    return node


class AgentToolset:
    """Bundles LangChain local CRUD, command/pkg, and DuckDuckGo web search tools."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        confirm_fn: ConfirmCallback | None = None,
        auto_approve: bool = False,
    ) -> None:
        self.workspace_root = workspace_root
        self.confirm_fn = confirm_fn
        self.auto_approve = auto_approve
        self._bypass_confirm = False
        self.tools: list[BaseTool] = [
            *make_local_tools(workspace_root, confirm_fn=self._dispatch_confirm),
            make_web_search_tool(),
            make_run_command_tool(
                workspace_root,
                confirm_fn=self._dispatch_confirm,
                auto_approve=auto_approve,
            ),
            make_pkg_tool(
                workspace_root,
                confirm_fn=self._dispatch_confirm,
                auto_approve=auto_approve,
            ),
        ]
        self._by_name: dict[str, BaseTool] = {t.name: t for t in self.tools}

    def _dispatch_confirm(self, action: str, target: str, preview: str | None) -> bool:
        """Delegate confirmation unless bypassed by the LangGraph safety gate."""
        if self._bypass_confirm or self.auto_approve or self.confirm_fn is None:
            return True
        return self.confirm_fn(action, target, preview)

    def set_auto_approve(self, auto_approve: bool) -> None:
        """Propagate auto-approve toggle to execution tools at runtime."""
        self.auto_approve = auto_approve
        from valkyria.tools.pkg_manager import make_pkg_tool as _pkg
        from valkyria.tools.run_command import make_run_command_tool as _run

        new_run = _run(
            self.workspace_root,
            confirm_fn=self._dispatch_confirm,
            auto_approve=auto_approve,
        )
        new_pkg = _pkg(
            self.workspace_root,
            confirm_fn=self._dispatch_confirm,
            auto_approve=auto_approve,
        )
        for t in (new_run, new_pkg):
            self._by_name[t.name] = t
        names = {t.name for t in (new_run, new_pkg)}
        self.tools = [t for t in self.tools if t.name not in names] + [new_run, new_pkg]

    def openai_tools(self) -> list[dict[str, Any]]:
        """Convert LangChain tools to OpenAI-compatible tool definitions."""
        return [convert_to_openai_tool(t) for t in self.tools]

    def gemini_declarations(self) -> list[dict[str, Any]]:
        """Convert LangChain tools to Gemini functionDeclarations payload."""
        declarations: list[dict[str, Any]] = []
        for spec in self.openai_tools():
            fn = spec.get("function", {})
            params = _sanitize_gemini_schema(fn.get("parameters", {"type": "object"}))
            declarations.append(
                {
                    "name": fn.get("name", ""),
                    "description": fn.get("description", ""),
                    "parameters": params,
                }
            )
        return declarations

    def execute_preapproved(self, name: str, raw_args: dict[str, Any] | str) -> tuple[bool, str]:
        """Execute a tool whose approval was already granted by the LangGraph safety gate."""
        prev = self._bypass_confirm
        self._bypass_confirm = True
        try:
            return self.execute(name, raw_args)
        finally:
            self._bypass_confirm = prev

    def execute(self, name: str, raw_args: dict[str, Any] | str) -> tuple[bool, str]:
        """Execute a registered LangChain tool safely and return (ok, output)."""
        tool_obj = self._by_name.get(name)
        if tool_obj is None:
            msg = f"Unknown tool '{name}'."
            render_tool_card(tool="tool", status="error", target=name, summary=msg)
            return False, msg

        parsed_args: dict[str, Any]
        if isinstance(raw_args, str):
            try:
                loaded = json.loads(raw_args) if raw_args.strip() else {}
                parsed_args = loaded if isinstance(loaded, dict) else {}
            except json.JSONDecodeError as exc:
                msg = f"Invalid JSON arguments for '{name}': {exc}"
                render_tool_card(tool="tool", status="error", target=name, summary=msg)
                return False, msg
        else:
            parsed_args = dict(raw_args)

        try:
            result = tool_obj.invoke(parsed_args)
            return True, str(result)
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            target_label = str(parsed_args.get("path") or parsed_args.get("query") or name)
            render_tool_card(tool=name, status="error", target=target_label, summary=err)
            return False, f"Error running {name}: {err}"

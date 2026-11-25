"""
Agent toolset — exports LangChain tools as OpenAI and Gemini function schemas and runs calls.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain_core.utils.function_calling import convert_to_openai_tool

from valkyrie.core.cards import render_tool_card
from valkyrie.tools.local_fs import ConfirmCallback, make_local_tools
from valkyrie.tools.web_search import make_web_search_tool

if TYPE_CHECKING:
    from pathlib import Path

    from langchain_core.tools import BaseTool


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
    """Bundles LangChain local CRUD + DuckDuckGo web search tools for streaming agents."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        confirm_fn: ConfirmCallback | None = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.confirm_fn = confirm_fn
        self.tools: list[BaseTool] = [
            *make_local_tools(workspace_root, confirm_fn=confirm_fn),
            make_web_search_tool(),
        ]
        self._by_name: dict[str, BaseTool] = {t.name: t for t in self.tools}

    def openai_tools(self) -> list[dict[str, Any]]:
        """Convert LangChain tools to OpenAI-compatible tool definitions (Groq / NVIDIA)."""
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


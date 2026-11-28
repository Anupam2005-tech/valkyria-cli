"""
Web search tool powered by LangChain's DuckDuckGo integration.
"""

from __future__ import annotations

import warnings
from typing import Any

from langchain_core.tools import BaseTool, tool

from valkyria.core.cards import render_tool_card


def run_duckduckgo_search(query: str, *, max_results: int = 5) -> list[dict[str, str]]:
    """Query DuckDuckGo via LangChain's DuckDuckGoSearchAPIWrapper."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

        wrapper = DuckDuckGoSearchAPIWrapper(max_results=max_results)
        raw: Any = wrapper.results(query, max_results=max_results)

    results: list[dict[str, str]] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": str(item.get("title", "")).strip(),
                "link": str(item.get("link", "")).strip(),
                "snippet": str(item.get("snippet", "")).strip(),
            }
        )
    return results


def make_web_search_tool() -> BaseTool:
    """Create the LangChain web_search BaseTool backed by DuckDuckGo."""

    @tool("web_search")
    def web_search_tool(query: str, max_results: int = 5) -> str:
        """Search the live web using DuckDuckGo (via LangChain) for current info, docs, or news."""
        results = run_duckduckgo_search(query, max_results=max(1, min(max_results, 10)))
        if not results:
            render_tool_card(
                tool="web",
                status="ok",
                target=query,
                summary="0 DuckDuckGo results returned",
            )
            return f"No web results found for '{query}'."

        card_preview = "\n".join(
            f"▸ {r['title'] or r['link']}" for r in results[:4]
        )
        render_tool_card(
            tool="web",
            status="ok",
            target=query,
            summary=f"{len(results)} DuckDuckGo result(s) via LangChain",
            details=card_preview,
        )

        formatted: list[str] = []
        for idx, item in enumerate(results, start=1):
            formatted.append(
                f"[{idx}] {item['title']}\nURL: {item['link']}\n{item['snippet']}"
            )
        return "\n\n".join(formatted)

    return web_search_tool


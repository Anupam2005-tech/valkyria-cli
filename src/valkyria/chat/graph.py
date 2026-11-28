"""
LangGraph multi-node agent graph: Planner -> Safety Gate -> Executor <-> Tools -> Evaluator.

Supports both direct interactive tool execution (`mode="direct"`) and full planned execution
(`mode="plan"` via `/plan`), with LangGraph `interrupt()` checkpoints for plan & tool approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from valkyria.chat import clients
from valkyria.tools.registry import MUTATING_TOOLS

if TYPE_CHECKING:
    from collections.abc import Callable

    from langchain_core.language_models.chat_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

    from valkyria.core.config import ValkyriaConfig
    from valkyria.tools.registry import AgentToolset

_PLAN_STEP_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.+)$")

_PLANNER_PROMPT = (
    "You are Valkyria's Planner.\n"
    "Produce a concise, actionable numbered execution plan (3 to 8 concrete steps) "
    "for the user's goal using the available workspace tools "
    "(read_file, write_file, edit_file, delete_file, list_directory, search_files, "
    "web_search, run_command, pkg_install).\n"
    "Format your output strictly as a brief 1-sentence summary followed by numbered steps "
    "(`1. ...`, `2. ...`). Do NOT execute tools or write full file contents yet."
)

_EVALUATOR_PROMPT = (
    "You are Valkyria's Evaluator.\n"
    "Compare the approved execution plan against the actual tool outputs and final response.\n"
    "If all planned steps succeeded and the user's goal is satisfied, reply starting with:\n"
    "PASS: <one concise sentence summarizing verification>\n"
    "Only if concrete steps failed or remain unfinished, reply starting with:\n"
    "RETRY: <concise instruction for what the Executor must fix>"
)


class AgentGraphState(TypedDict):
    """Typed state carried across all LangGraph nodes and JSON checkpoints."""

    messages: Annotated[list[BaseMessage], add_messages]
    mode: Literal["direct", "plan"]
    goal: str
    plan_text: str
    plan_steps: list[str]
    plan_approved: bool
    plan_cancelled: bool
    plan_feedback: str
    iteration: int
    max_iterations: int
    eval_attempts: int
    max_eval_attempts: int
    evaluation_passed: bool
    evaluation_notes: str
    approved_tool_call_ids: list[str]
    denied_tool_call_ids: list[str]
    tools_enabled: bool


@dataclass
class GraphRuntime:
    """Mutable runtime dependencies injected into graph nodes outside checkpointed state."""

    config: ValkyriaConfig
    api_keys: dict[str, str]
    get_active_model: Callable[[], str]
    toolset: AgentToolset
    is_auto_approved: Callable[[], bool]
    record_checkpoint: Callable[[str, dict[str, Any]], None] | None = None

    def resolve_role_model(self, role: str) -> tuple[str, str, str]:
        """Pick (qualified_id, provider_key, model_id) for planner, executor, or evaluator."""
        active = self.get_active_model()
        candidate: str | None = None
        if role == "planner":
            candidate = self.config.models.planner
        elif role == "code":
            candidate = self.config.models.code
        elif role == "evaluator":
            candidate = self.config.models.planner

        chosen = active
        if candidate and "/" in candidate:
            pkey, _ = candidate.split("/", 1)
            if pkey in self.api_keys:
                chosen = candidate

        provider_key, _, model_id = chosen.partition("/")
        return chosen, provider_key, model_id

    def build_model(self, role: str, *, temperature: float) -> tuple[str, str, BaseChatModel]:
        """Instantiate the LangChain chat model for a graph role."""
        _, provider_key, model_id = self.resolve_role_model(role)
        api_key = self.api_keys.get(provider_key, "")
        if not api_key:
            raise clients.ChatStreamError(
                f"No API key available for provider '{provider_key}'."
            )
        model = clients.build_chat_model(
            provider_key=provider_key,
            model_id=model_id,
            api_key=api_key,
            temperature=temperature,
            streaming=True,
        )
        return provider_key, model_id, model


def parse_plan_steps(plan_text: str) -> list[str]:
    """Extract numbered or bulleted plan steps from planner output."""
    steps: list[str] = []
    for line in plan_text.splitlines():
        m = _PLAN_STEP_RE.match(line)
        if m:
            step = m.group(1).strip()
            if step:
                steps.append(step)
    return steps


def _coalesce_system_messages(
    messages: list[BaseMessage],
    extra_system: str | None = None,
) -> list[BaseMessage]:
    """Combine SystemMessages at the front so Gemini and OpenAI-style models stay aligned."""
    sys_parts: list[str] = []
    rest: list[BaseMessage] = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            txt = str(msg.text) if hasattr(msg, "text") else str(msg.content)
            if txt.strip():
                sys_parts.append(txt)
        else:
            rest.append(msg)
    if extra_system and extra_system.strip():
        sys_parts.append(extra_system.strip())
    if sys_parts:
        return [SystemMessage(content="\n\n".join(sys_parts)), *rest]
    return rest


def _last_ai_message(messages: list[BaseMessage]) -> AIMessage | None:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return msg
    return None


def build_agent_graph(
    runtime: GraphRuntime,
    *,
    checkpointer: BaseCheckpointSaver[Any],
) -> CompiledStateGraph[Any]:
    """Compile the multi-node LangGraph pipeline with JSON checkpointing."""

    def route_entry(state: AgentGraphState) -> str:
        return "planner" if state.get("mode") == "plan" else "executor"

    async def planner_node(state: AgentGraphState) -> dict[str, Any]:
        provider_key, model_id, model = runtime.build_model("planner", temperature=0.3)
        history = _coalesce_system_messages(state["messages"], extra_system=_PLANNER_PROMPT)
        try:
            response = await model.ainvoke(history)
        except Exception as exc:
            raise clients.parse_langchain_error(
                exc,
                provider_key=provider_key,
                model_id=model_id,
            ) from exc

        plan_text = str(response.text) if hasattr(response, "text") else str(response.content)
        steps = parse_plan_steps(plan_text)
        return {
            "plan_text": plan_text,
            "plan_steps": steps,
            "plan_approved": False,
            "plan_cancelled": False,
            "messages": [response],
        }

    def plan_safety_gate_node(state: AgentGraphState) -> dict[str, Any]:
        if runtime.is_auto_approved():
            return {"plan_approved": True, "plan_cancelled": False}

        decision = interrupt(
            {
                "kind": "plan_approval",
                "goal": state.get("goal", ""),
                "plan_text": state.get("plan_text", ""),
                "steps": state.get("plan_steps", []),
            }
        )

        action = "deny"
        feedback = ""
        if decision is True or decision == "approve":
            action = "approve"
        elif isinstance(decision, dict):
            action = str(decision.get("action", "deny")).lower()
            feedback = str(decision.get("feedback", "")).strip()

        if action == "approve":
            return {"plan_approved": True, "plan_cancelled": False}
        if action == "edit":
            revision_prompt = (
                f"Revise the plan based on this user feedback:\n{feedback or 'Clarify the steps.'}"
            )
            return {
                "plan_approved": False,
                "plan_cancelled": False,
                "plan_feedback": feedback,
                "messages": [HumanMessage(content=revision_prompt)],
            }
        return {
            "plan_approved": False,
            "plan_cancelled": True,
            "messages": [AIMessage(content="Plan cancelled by user.")],
        }

    def route_after_plan_gate(state: AgentGraphState) -> str:
        if state.get("plan_cancelled"):
            return str(END)
        if state.get("plan_approved"):
            return "executor"
        return "planner"

    async def executor_node(state: AgentGraphState) -> dict[str, Any]:
        role = "code" if state.get("mode") == "plan" else "executor"
        provider_key, model_id, model = runtime.build_model(role, temperature=0.7)
        tools_enabled = state.get("tools_enabled", True)

        extra_plan_note: str | None = None
        if state.get("mode") == "plan" and state.get("plan_text"):
            extra_plan_note = (
                "Execute this approved plan using your tools and report exact results:\n"
                f"{state['plan_text']}"
            )
        exec_messages = _coalesce_system_messages(state["messages"], extra_system=extra_plan_note)

        while True:
            runnable = (
                clients.bind_model_tools(model, runtime.toolset.tools)
                if tools_enabled
                else model
            )
            try:
                response = await runnable.ainvoke(exec_messages)
                break
            except Exception as exc:
                err = clients.parse_langchain_error(
                    exc,
                    provider_key=provider_key,
                    model_id=model_id,
                )
                err_lower = str(err).lower()
                if (
                    tools_enabled
                    and err.status_code == 400
                    and any(k in err_lower for k in ("tool", "function"))
                ):
                    tools_enabled = False
                    continue
                raise err from exc

        return {
            "messages": [response],
            "iteration": state.get("iteration", 0) + 1,
            "tools_enabled": tools_enabled,
        }

    def route_after_executor(state: AgentGraphState) -> str:
        last_ai = _last_ai_message(state["messages"])
        if (
            last_ai is not None
            and last_ai.tool_calls
            and state.get("iteration", 0) < state.get("max_iterations", 8)
        ):
            return "tool_safety_gate"
        if state.get("mode") == "plan":
            return "evaluator"
        return str(END)

    def tool_safety_gate_node(state: AgentGraphState) -> dict[str, Any]:
        last_ai = _last_ai_message(state["messages"])
        if last_ai is None or not last_ai.tool_calls:
            return {"approved_tool_call_ids": [], "denied_tool_call_ids": []}

        all_ids = [str(tc.get("id") or f"call_{i}") for i, tc in enumerate(last_ai.tool_calls)]
        mutating_calls = [
            {
                "id": str(tc.get("id") or f"call_{i}"),
                "name": str(tc.get("name", "")),
                "args": dict(tc.get("args") or {}),
            }
            for i, tc in enumerate(last_ai.tool_calls)
            if str(tc.get("name", "")) in MUTATING_TOOLS
        ]

        if not mutating_calls or runtime.is_auto_approved():
            return {"approved_tool_call_ids": all_ids, "denied_tool_call_ids": []}

        decision = interrupt({"kind": "tool_approval", "calls": mutating_calls})

        if decision is True:
            return {"approved_tool_call_ids": all_ids, "denied_tool_call_ids": []}
        if decision is False or decision is None:
            mutating_ids = {c["id"] for c in mutating_calls}
            approved = [cid for cid in all_ids if cid not in mutating_ids]
            return {"approved_tool_call_ids": approved, "denied_tool_call_ids": list(mutating_ids)}
        if isinstance(decision, dict):
            approved_set = set(str(x) for x in decision.get("approved_ids", []))
            denied_set = set(str(x) for x in decision.get("denied_ids", []))
            for cid in all_ids:
                if cid not in approved_set and cid not in denied_set:
                    approved_set.add(cid)
            return {
                "approved_tool_call_ids": list(approved_set),
                "denied_tool_call_ids": list(denied_set),
            }
        return {"approved_tool_call_ids": all_ids, "denied_tool_call_ids": []}

    def tools_node(state: AgentGraphState) -> dict[str, Any]:
        last_ai = _last_ai_message(state["messages"])
        if last_ai is None or not last_ai.tool_calls:
            return {"messages": []}

        denied = set(state.get("denied_tool_call_ids", []))
        tool_messages: list[ToolMessage] = []

        for idx, tc in enumerate(last_ai.tool_calls):
            call_id = str(tc.get("id") or f"call_{idx}")
            name = str(tc.get("name", ""))
            args = dict(tc.get("args") or {})
            if call_id in denied:
                tool_messages.append(
                    ToolMessage(
                        content=f"User declined {name} action.",
                        name=name,
                        tool_call_id=call_id,
                    )
                )
                continue

            if name in MUTATING_TOOLS and runtime.record_checkpoint is not None:
                runtime.record_checkpoint(name, args)

            _, output = runtime.toolset.execute_preapproved(name, args)
            tool_messages.append(
                ToolMessage(
                    content=output,
                    name=name,
                    tool_call_id=call_id,
                )
            )

        return {"messages": tool_messages}

    def route_after_tools(state: AgentGraphState) -> str:
        if state.get("iteration", 0) >= state.get("max_iterations", 8):
            return "evaluator" if state.get("mode") == "plan" else str(END)
        return "executor"

    async def evaluator_node(state: AgentGraphState) -> dict[str, Any]:
        provider_key, model_id, model = runtime.build_model("evaluator", temperature=0.1)
        last_ai = _last_ai_message(state["messages"])
        final_summary = (
            str(last_ai.text)
            if (last_ai is not None and hasattr(last_ai, "text"))
            else str(last_ai.content if last_ai else "")
        )
        tool_trace = [
            f"- {m.name}: {str(m.content)[:240]}"
            for m in state["messages"]
            if isinstance(m, ToolMessage)
        ]
        eval_input = [
            SystemMessage(content=_EVALUATOR_PROMPT),
            HumanMessage(
                content=(
                    f"Goal: {state.get('goal', '')}\n\n"
                    f"Approved Plan:\n{state.get('plan_text', '')}\n\n"
                    f"Tool Outputs:\n" + ("\n".join(tool_trace) or "(none)") + "\n\n"
                    f"Executor Response:\n{final_summary[:1200]}"
                )
            ),
        ]
        try:
            response = await model.ainvoke(eval_input)
        except Exception as exc:
            raise clients.parse_langchain_error(
                exc,
                provider_key=provider_key,
                model_id=model_id,
            ) from exc

        eval_text = (
            str(response.text) if hasattr(response, "text") else str(response.content)
        ).strip()
        upper = eval_text.upper()
        attempts = state.get("eval_attempts", 0)
        max_attempts = state.get("max_eval_attempts", 1)

        if upper.startswith("RETRY") and attempts < max_attempts:
            return {
                "evaluation_passed": False,
                "evaluation_notes": eval_text,
                "eval_attempts": attempts + 1,
                "messages": [
                    HumanMessage(
                        content=(
                            f"Evaluator found incomplete or failing work:\n{eval_text}\n"
                            "Please complete the remaining steps."
                        )
                    )
                ],
            }

        return {
            "evaluation_passed": True,
            "evaluation_notes": eval_text,
        }

    def route_after_evaluator(state: AgentGraphState) -> str:
        if state.get("evaluation_passed", True):
            return str(END)
        if state.get("iteration", 0) >= state.get("max_iterations", 8):
            return str(END)
        return "executor"

    graph = StateGraph(AgentGraphState)
    graph.add_node("planner", planner_node)
    graph.add_node("plan_safety_gate", plan_safety_gate_node)
    graph.add_node("executor", executor_node)
    graph.add_node("tool_safety_gate", tool_safety_gate_node)
    graph.add_node("tools", tools_node)
    graph.add_node("evaluator", evaluator_node)

    graph.add_conditional_edges(
        START,
        route_entry,
        {"planner": "planner", "executor": "executor"},
    )
    graph.add_edge("planner", "plan_safety_gate")
    graph.add_conditional_edges(
        "plan_safety_gate",
        route_after_plan_gate,
        {"executor": "executor", "planner": "planner", str(END): END},
    )
    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {"tool_safety_gate": "tool_safety_gate", "evaluator": "evaluator", str(END): END},
    )
    graph.add_edge("tool_safety_gate", "tools")
    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {"executor": "executor", "evaluator": "evaluator", str(END): END},
    )
    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluator,
        {"executor": "executor", str(END): END},
    )

    return graph.compile(checkpointer=checkpointer)


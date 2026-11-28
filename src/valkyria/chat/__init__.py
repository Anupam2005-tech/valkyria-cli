"""Chat engine — LangGraph workflow, LangChain models, message protocol, renderer, and REPL."""

from valkyria.chat.clients import (
    ChatStreamError,
    StreamChunk,
    build_chat_model,
    parse_langchain_error,
    stream_chat_completion,
)
from valkyria.chat.commands import SlashCommand, SlashCommandRegistry, ValkyriaCompleter
from valkyria.chat.engine import (
    ChatEngine,
    build_command_registry,
    build_system_prompt,
    run_chat_repl,
)
from valkyria.chat.graph import AgentGraphState, GraphRuntime, build_agent_graph
from valkyria.chat.messages import (
    ChatMessage,
    ContextBudget,
    MessageRole,
    TokenUsage,
    estimate_messages_tokens,
    estimate_tokens,
)

__all__ = [
    "AgentGraphState",
    "ChatEngine",
    "ChatMessage",
    "ChatStreamError",
    "ContextBudget",
    "GraphRuntime",
    "MessageRole",
    "SlashCommand",
    "SlashCommandRegistry",
    "StreamChunk",
    "TokenUsage",
    "ValkyriaCompleter",
    "build_agent_graph",
    "build_chat_model",
    "build_command_registry",
    "build_system_prompt",
    "estimate_messages_tokens",
    "estimate_tokens",
    "parse_langchain_error",
    "run_chat_repl",
    "stream_chat_completion",
]

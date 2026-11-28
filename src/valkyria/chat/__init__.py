"""Chat engine — message protocol, streaming clients, renderer, and REPL."""

from valkyrie.chat.clients import ChatStreamError, StreamChunk, stream_chat_completion
from valkyrie.chat.commands import SlashCommand, SlashCommandRegistry, ValkyrieCompleter
from valkyrie.chat.engine import (
    ChatEngine,
    build_command_registry,
    build_system_prompt,
    run_chat_repl,
)
from valkyrie.chat.messages import (
    ChatMessage,
    ContextBudget,
    MessageRole,
    TokenUsage,
    estimate_messages_tokens,
    estimate_tokens,
)

__all__ = [
    "ChatEngine",
    "ChatMessage",
    "ChatStreamError",
    "ContextBudget",
    "MessageRole",
    "SlashCommand",
    "SlashCommandRegistry",
    "StreamChunk",
    "TokenUsage",
    "ValkyrieCompleter",
    "build_command_registry",
    "build_system_prompt",
    "estimate_messages_tokens",
    "estimate_tokens",
    "run_chat_repl",
    "stream_chat_completion",
]

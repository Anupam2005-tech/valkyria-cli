"""
Provider abstraction — base protocol for all model providers.

Each provider must be able to validate its API key, fetch a catalog
of available models, and tag each model with its capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class ModelCapability(StrEnum):
    """Capabilities a model can have, mapped to assignment roles."""

    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    EMBEDDINGS = "embeddings"


# Roles that models can be assigned to
ASSIGNABLE_ROLES = ["chat", "code", "planner", "vision", "summarization", "embeddings"]


@dataclass
class ModelInfo:
    """Information about a single model from a provider."""

    id: str  # Provider's model ID (e.g. "llama-3.3-70b-versatile")
    name: str  # Display name
    provider: str  # Provider key (e.g. "groq")
    capabilities: list[ModelCapability] = field(default_factory=list)
    context_window: int | None = None  # Max tokens
    description: str = ""
    is_active: bool = True

    @property
    def qualified_id(self) -> str:
        """Full provider/model identifier (e.g. 'groq/llama-3.3-70b-versatile')."""
        return f"{self.provider}/{self.id}"

    def supports_role(self, role: str) -> bool:
        """Check if this model can serve a given role."""
        if role == "embeddings":
            return ModelCapability.EMBEDDINGS in self.capabilities
        if role == "vision":
            return ModelCapability.VISION in self.capabilities
        # chat, code, planner, summarization — any text model works
        return (
            ModelCapability.CHAT in self.capabilities
            or ModelCapability.CODE in self.capabilities
        )


class Provider(Protocol):
    """Protocol that all providers must implement."""

    @property
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    def key(self) -> str:
        """Provider key (e.g. 'groq')."""
        ...

    async def validate_key(self, api_key: str) -> bool:
        """Validate that the API key is working. Returns True if valid."""
        ...

    async def fetch_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch the catalog of available models for this key."""
        ...


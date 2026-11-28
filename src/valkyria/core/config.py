"""
Configuration management — load, save, and validate user config.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from valkyria.core.paths import get_config_path

if TYPE_CHECKING:
    from pathlib import Path


class UserProfile(BaseModel):
    """Optional user profile information."""

    name: str | None = None
    profession: str | None = None
    expertise: str | None = None  # "beginner", "intermediate", "advanced"


class ModelAssignment(BaseModel):
    """Model-to-role mapping."""

    chat: str | None = None  # "provider/model"
    code: str | None = None
    planner: str | None = None
    vision: str | None = None
    summarization: str | None = None
    embeddings: str | None = None


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""

    name: str
    enabled: bool = True


class PineconeConfig(BaseModel):
    """Configuration for Pinecone vector DB (RAG)."""

    index_name: str = "valkyria-rag"
    cloud: str = "aws"
    region: str = "us-east-1"


class ValkyriaConfig(BaseModel):
    """Root configuration schema."""

    version: int = 1
    first_run_complete: bool = False
    profile: UserProfile = Field(default_factory=UserProfile)
    models: ModelAssignment = Field(default_factory=ModelAssignment)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    pinecone: PineconeConfig = Field(default_factory=PineconeConfig)
    embedding_mode: str = "pinecone"  # "pinecone", "hosted", or "unassigned"
    sync_enabled: bool = False
    feature_flags: dict[str, bool] = Field(default_factory=dict)

    @classmethod
    def load(cls) -> ValkyriaConfig:
        """Load config from disk, or return defaults if not found."""
        path = get_config_path()
        if path.exists():
            data: dict[str, Any] = json.loads(path.read_text())
            return cls.model_validate(data)
        return cls()

    def save(self) -> Path:
        """Save config to disk and return the path."""
        path = get_config_path()
        path.write_text(self.model_dump_json(indent=2) + "\n")
        return path

    @property
    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return not self.first_run_complete


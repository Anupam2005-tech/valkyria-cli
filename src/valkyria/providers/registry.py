"""
Unified model registry — aggregates, caches, and queries provider catalogs.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from valkyrie.core.paths import get_models_cache_path
from valkyrie.providers.base import ModelCapability, ModelInfo, Provider
from valkyrie.providers.gemini import GeminiProvider
from valkyrie.providers.groq import GroqProvider
from valkyrie.providers.nvidia import NvidiaProvider

PROVIDERS: dict[str, Provider] = {
    "groq": GroqProvider(),
    "gemini": GeminiProvider(),
    "nvidia": NvidiaProvider(),
}


_VERSION_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _model_sort_key(model: ModelInfo) -> tuple[str, int, float, int, str]:
    """
    Sort models within each provider so active, newer flagship models rank first.

    Demotes legacy/preview/experimental specialized builds below current stable models.
    """
    lower_id = model.id.lower()
    active_rank = 0 if model.is_active else 1

    # Extract highest numeric version hint (e.g. 4.0, 3.8, 3.3, 2.5)
    nums = [float(x) for x in _VERSION_RE.findall(lower_id) if float(x) < 20]
    ver_score = -max(nums) if nums else 0.0

    # Prefer non-preview/non-legacy general models over niche variants
    penalty = 0
    if any(k in lower_id for k in ("preview", "legacy", "experimental", "deep-research")):
        penalty += 2
    if any(k in lower_id for k in ("gemini-2.0", "gemini-1.5", "gemini-2.5")):
        penalty += 3
    if any(k in lower_id for k in ("flash", "pro", "hydrogen", "argon", "120b", "70b")):
        penalty -= 1

    return (model.provider, active_rank, ver_score, penalty, lower_id)


def get_provider(key: str) -> Provider | None:
    """Return the provider instance for a provider key."""
    return PROVIDERS.get(key.lower())


class ModelRegistry:
    """Unified catalog of discovered models across configured providers."""

    def __init__(
        self,
        models: dict[str, ModelInfo] | None = None,
        updated_at: str | None = None,
    ) -> None:
        self.models: dict[str, ModelInfo] = models or {}
        self.updated_at: str | None = updated_at

    @classmethod
    def load_cache(cls) -> ModelRegistry:
        """Load cached model catalog from disk, or return an empty registry."""
        path = get_models_cache_path()
        if not path.exists():
            return cls()

        try:
            raw: dict[str, Any] = json.loads(path.read_text())
        except json.JSONDecodeError:
            return cls()

        models: dict[str, ModelInfo] = {}
        for item in raw.get("models", []):
            try:
                caps = [ModelCapability(c) for c in item.get("capabilities", [])]
                info = ModelInfo(
                    id=item["id"],
                    name=item.get("name", item["id"]),
                    provider=item["provider"],
                    capabilities=caps,
                    context_window=item.get("context_window"),
                    description=item.get("description", ""),
                    is_active=item.get("is_active", True),
                )
                models[info.qualified_id] = info
            except (KeyError, ValueError):
                continue

        return cls(models=models, updated_at=raw.get("updated_at"))

    def save_cache(self) -> None:
        """Persist the current model catalog to disk."""
        path = get_models_cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": self.updated_at or datetime.now(UTC).isoformat(),
            "models": [
                {
                    **asdict(m),
                    "capabilities": [c.value for c in m.capabilities],
                }
                for m in self.models.values()
            ],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")

    async def validate_and_fetch(
        self, provider_key: str, api_key: str
    ) -> tuple[bool, list[ModelInfo]]:
        """Validate a provider key and fetch its model catalog."""
        provider = get_provider(provider_key)
        if provider is None:
            return False, []

        is_valid = await provider.validate_key(api_key)
        if not is_valid:
            return False, []

        fetched = await provider.fetch_models(api_key)
        return True, fetched

    async def refresh(
        self, api_keys: dict[str, str]
    ) -> dict[str, tuple[bool, int]]:
        """
        Fetch catalogs concurrently for all provided API keys.

        Replaces cached models for the queried providers and saves the cache.
        Returns a mapping of provider_key -> (valid, model_count).
        """
        keys_to_query = [(k, v) for k, v in api_keys.items() if k in PROVIDERS and v]
        if not keys_to_query:
            return {}

        tasks = [self.validate_and_fetch(pkey, key) for pkey, key in keys_to_query]
        results = await asyncio.gather(*tasks)

        summary: dict[str, tuple[bool, int]] = {}
        for (pkey, _), (valid, fetched) in zip(keys_to_query, results, strict=True):
            # Remove stale entries for this provider before inserting new ones
            stale = [qid for qid, m in self.models.items() if m.provider == pkey]
            for qid in stale:
                del self.models[qid]

            for m in fetched:
                self.models[m.qualified_id] = m

            summary[pkey] = (valid, len(fetched))

        self.updated_at = datetime.now(UTC).isoformat()
        self.save_cache()
        return summary

    def get_model(self, qualified_id: str) -> ModelInfo | None:
        """Look up a model by its 'provider/model' qualified ID."""
        return self.models.get(qualified_id)

    def list_models(
        self,
        *,
        provider: str | None = None,
        capability: ModelCapability | None = None,
        role: str | None = None,
        search: str | None = None,
    ) -> list[ModelInfo]:
        """Return matching models sorted by provider and ranked relevance."""
        needle = search.strip().lower() if search else None
        results: list[ModelInfo] = []
        for m in self.models.values():
            if provider is not None and m.provider != provider.lower():
                continue
            if capability is not None and capability not in m.capabilities:
                continue
            if role is not None and not m.supports_role(role):
                continue
            if needle and needle not in m.qualified_id.lower() and needle not in m.name.lower():
                continue
            results.append(m)

        return sorted(results, key=_model_sort_key)

    def provider_counts(self) -> dict[str, int]:
        """Return cached model counts grouped by provider."""
        counts: dict[str, int] = {}
        for m in self.models.values():
            counts[m.provider] = counts.get(m.provider, 0) + 1
        return dict(sorted(counts.items()))

    def resolve_model(
        self,
        query: str,
        *,
        preferred_provider: str | None = None,
    ) -> tuple[ModelInfo | None, list[ModelInfo]]:
        """
        Resolve a qualified ('provider/model') or bare model ID/prefix.

        Returns (exact_or_unique_match, candidate_suggestions).
        """
        cleaned = query.strip()
        if not cleaned:
            return None, []

        exact = self.models.get(cleaned)
        if exact is not None:
            return exact, []

        lower = cleaned.lower()
        # Try exact model ID match (optionally biased to preferred_provider)
        id_matches = [m for m in self.models.values() if m.id.lower() == lower]
        if len(id_matches) == 1:
            return id_matches[0], []
        if id_matches and preferred_provider:
            scoped = [m for m in id_matches if m.provider == preferred_provider.lower()]
            if len(scoped) == 1:
                return scoped[0], []

        # Substring fallback for smart suggestions
        partial = self.list_models(search=cleaned)
        if len(partial) == 1 and "/" not in cleaned:
            return partial[0], []
        return None, partial[:8]

"""
Groq provider — fast inference for open models.

API docs: https://console.groq.com/docs/api-reference
Models endpoint: GET https://api.groq.com/openai/v1/models
"""

from __future__ import annotations

import httpx

from valkyria.providers.base import ModelCapability, ModelInfo

GROQ_API_BASE = "https://api.groq.com/openai/v1"

# Known capability hints for Groq models
_VISION_MODELS = {
    "llama-3.2-11b-vision-preview",
    "llama-3.2-90b-vision-preview",
    "meta-llama/llama-4-scout-17b-16e-instruct",
}
_EMBEDDING_MODELS: set[str] = set()  # Groq doesn't currently offer embeddings
_NON_CHAT_PREFIXES = (
    "whisper-",
    "canopylabs/orpheus",
    "meta-llama/llama-prompt-guard",
    "meta-llama/llama-guard",
)


class GroqProvider:
    """Groq inference provider."""

    @property
    def name(self) -> str:
        return "Groq"

    @property
    def key(self) -> str:
        return "groq"

    async def validate_key(self, api_key: str) -> bool:
        """Validate by listing models."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GROQ_API_BASE}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def fetch_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch Groq model catalog."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GROQ_API_BASE}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []

        models: list[ModelInfo] = []
        for item in data.get("data", []):
            model_id: str = item.get("id", "")
            if not model_id:
                continue
            if any(model_id.lower().startswith(prefix) for prefix in _NON_CHAT_PREFIXES):
                continue

            # Determine capabilities
            caps: list[ModelCapability] = []
            if model_id in _VISION_MODELS:
                caps.append(ModelCapability.VISION)
                caps.append(ModelCapability.CHAT)
            elif model_id in _EMBEDDING_MODELS:
                caps.append(ModelCapability.EMBEDDINGS)
            else:
                caps.append(ModelCapability.CHAT)
                caps.append(ModelCapability.CODE)

            ctx = item.get("context_window")

            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider="groq",
                    capabilities=caps,
                    context_window=ctx,
                    is_active=item.get("active", True),
                )
            )

        return models


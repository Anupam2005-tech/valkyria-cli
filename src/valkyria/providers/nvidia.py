"""
NVIDIA NIM provider — NVIDIA hosted inference.

NVIDIA NIM uses an OpenAI-compatible API.
API base: https://integrate.api.nvidia.com/v1
"""

from __future__ import annotations

import httpx

from valkyria.providers.base import ModelCapability, ModelInfo

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"

# Known vision models on NVIDIA NIM
_VISION_HINTS = {"microsoft/phi-4-multimodal-instruct", "google/gemma-3-27b-it"}
# Known embedding models
_EMBEDDING_HINTS = {
    "nvidia/nv-embedqa-e5-v5",
    "nvidia/nv-embedqa-mistral-7b-v2",
    "nvidia/llama-3.2-nv-embedqa-1b-v2",
    "baai/bge-m3",
    "snowflake/arctic-embed-l",
    "nvidia/embed-qa-4",
}


class NvidiaProvider:
    """NVIDIA NIM provider."""

    @property
    def name(self) -> str:
        return "NVIDIA NIM"

    @property
    def key(self) -> str:
        return "nvidia"

    async def validate_key(self, api_key: str) -> bool:
        """Validate by listing models."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{NVIDIA_API_BASE}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def fetch_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch NVIDIA model catalog."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{NVIDIA_API_BASE}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=15.0,
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

            caps: list[ModelCapability] = []

            if model_id in _EMBEDDING_HINTS:
                caps.append(ModelCapability.EMBEDDINGS)
            elif model_id in _VISION_HINTS:
                caps.append(ModelCapability.VISION)
                caps.append(ModelCapability.CHAT)
            else:
                caps.append(ModelCapability.CHAT)
                caps.append(ModelCapability.CODE)

            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider="nvidia",
                    capabilities=caps,
                    context_window=item.get("context_window"),
                )
            )

        return models


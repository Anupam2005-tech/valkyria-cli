"""
Gemini provider — Google's Gemini models.

API docs: https://ai.google.dev/api/models
Models endpoint: GET https://generativelanguage.googleapis.com/v1beta/models
"""

from __future__ import annotations

from typing import Any

import httpx

from valkyria.providers.base import ModelCapability, ModelInfo

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


_NON_CHAT_KEYWORDS = (
    "-tts",
    "-transcribe",
    "lyria",
    "imagen",
    "-image",
    "nano-banana",
    "robotics",
    "computer-use",
    "veo-",
    "aqa",
)

_VISION_PREFIXES = (
    "gemini-4",
    "gemini-3",
    "gemini-2",
    "gemini-1.5",
    "gemini-omni",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-pro-vision",
)


class GeminiProvider:
    """Google Gemini provider."""

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def key(self) -> str:
        return "gemini"

    async def validate_key(self, api_key: str) -> bool:
        """Validate by listing models."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GEMINI_API_BASE}/models",
                    params={"key": api_key},
                    timeout=10.0,
                )
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def fetch_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch Gemini model catalog."""
        all_models: list[ModelInfo] = []
        page_token: str | None = None

        try:
            async with httpx.AsyncClient() as client:
                while True:
                    params: dict[str, str] = {"key": api_key, "pageSize": "100"}
                    if page_token:
                        params["pageToken"] = page_token

                    resp = await client.get(
                        f"{GEMINI_API_BASE}/models",
                        params=params,
                        timeout=10.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("models", []):
                        model = self._parse_model(item)
                        if model is not None:
                            all_models.append(model)

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

        except httpx.HTTPError:
            pass

        return all_models

    def _parse_model(self, item: dict[str, Any]) -> ModelInfo | None:
        """Parse a single model entry from the Gemini API."""
        # Model name is like "models/gemini-3.8-flash"
        full_name: str = item.get("name", "")
        model_id = full_name.removeprefix("models/")
        if not model_id:
            return None

        lower_id = model_id.lower()
        methods: list[str] = item.get("supportedGenerationMethods", [])
        caps: list[ModelCapability] = []

        if "embedContent" in methods:
            caps.append(ModelCapability.EMBEDDINGS)
        elif "generateContent" in methods or "streamGenerateContent" in methods:
            # Skip specialized audio/music/image/TTS/robotics endpoints from text chat
            if any(kw in lower_id for kw in _NON_CHAT_KEYWORDS):
                return None

            caps.append(ModelCapability.CHAT)
            caps.append(ModelCapability.CODE)

            if any(lower_id.startswith(prefix) for prefix in _VISION_PREFIXES):
                caps.append(ModelCapability.VISION)

        if not caps:
            return None

        display_name: str = item.get("displayName", model_id)
        ctx = item.get("inputTokenLimit")

        return ModelInfo(
            id=model_id,
            name=display_name,
            provider="gemini",
            capabilities=caps,
            context_window=ctx,
            description=item.get("description", ""),
        )


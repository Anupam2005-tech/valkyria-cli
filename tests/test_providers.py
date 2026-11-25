"""Tests for provider discovery, model registry, and model CLI commands."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from valkyrie.cli.main import cli
from valkyrie.providers.base import ModelCapability, ModelInfo
from valkyrie.providers.gemini import GeminiProvider
from valkyrie.providers.groq import GroqProvider
from valkyrie.providers.nvidia import NvidiaProvider
from valkyrie.providers.registry import ModelRegistry

if TYPE_CHECKING:
    from pathlib import Path


class TestModelInfo:
    """Tests for ModelInfo capability & role checks."""

    def test_supports_role_text_model(self) -> None:
        m = ModelInfo(
            id="llama-3.3-70b-versatile",
            name="Llama 3.3 70B",
            provider="groq",
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE],
        )
        assert m.qualified_id == "groq/llama-3.3-70b-versatile"
        assert m.supports_role("chat") is True
        assert m.supports_role("code") is True
        assert m.supports_role("planner") is True
        assert m.supports_role("summarization") is True
        assert m.supports_role("vision") is False
        assert m.supports_role("embeddings") is False

    def test_supports_role_embedding_model(self) -> None:
        m = ModelInfo(
            id="text-embedding-004",
            name="Text Embedding 004",
            provider="gemini",
            capabilities=[ModelCapability.EMBEDDINGS],
        )
        assert m.supports_role("embeddings") is True
        assert m.supports_role("chat") is False
        assert m.supports_role("vision") is False

    def test_supports_role_vision_model(self) -> None:
        m = ModelInfo(
            id="gemini-2.0-flash",
            name="Gemini 2.0 Flash",
            provider="gemini",
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.VISION],
        )
        assert m.supports_role("vision") is True
        assert m.supports_role("chat") is True


class TestProviderClients:
    """Tests for Groq, Gemini, and NVIDIA provider parsing."""

    def test_groq_fetch_models(self) -> None:
        payload = {
            "data": [
                {"id": "llama-3.3-70b-versatile", "context_window": 131072, "active": True},
                {"id": "llama-3.2-11b-vision-preview", "context_window": 8192, "active": True},
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("valkyrie.providers.groq.httpx.AsyncClient", return_value=mock_client):
            models = asyncio.run(GroqProvider().fetch_models("gsk_test"))

        assert len(models) == 2
        assert models[0].qualified_id == "groq/llama-3.3-70b-versatile"
        assert models[0].context_window == 131072
        assert ModelCapability.VISION in models[1].capabilities

    def test_gemini_fetch_models(self) -> None:
        payload = {
            "models": [
                {
                    "name": "models/gemini-2.0-flash",
                    "displayName": "Gemini 2.0 Flash",
                    "supportedGenerationMethods": ["generateContent", "streamGenerateContent"],
                    "inputTokenLimit": 1048576,
                },
                {
                    "name": "models/text-embedding-004",
                    "displayName": "Text Embedding 004",
                    "supportedGenerationMethods": ["embedContent"],
                    "inputTokenLimit": 2048,
                },
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("valkyrie.providers.gemini.httpx.AsyncClient", return_value=mock_client):
            models = asyncio.run(GeminiProvider().fetch_models("AIza_test"))

        assert len(models) == 2
        assert models[0].qualified_id == "gemini/gemini-2.0-flash"
        assert ModelCapability.VISION in models[0].capabilities
        assert models[1].qualified_id == "gemini/text-embedding-004"
        assert models[1].capabilities == [ModelCapability.EMBEDDINGS]

    def test_nvidia_fetch_models(self) -> None:
        payload = {
            "data": [
                {"id": "meta/llama-3.1-70b-instruct"},
                {"id": "nvidia/nv-embedqa-e5-v5"},
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("valkyrie.providers.nvidia.httpx.AsyncClient", return_value=mock_client):
            models = asyncio.run(NvidiaProvider().fetch_models("nvapi-test"))

        assert len(models) == 2
        assert ModelCapability.CHAT in models[0].capabilities
        assert models[1].capabilities == [ModelCapability.EMBEDDINGS]

    def test_filters_non_chat_gemini_and_groq_utilities(self) -> None:
        gemini_payload = {
            "models": [
                {
                    "name": "models/gemini-3.8-flash",
                    "displayName": "Gemini 3.8 Flash",
                    "supportedGenerationMethods": ["generateContent", "streamGenerateContent"],
                    "inputTokenLimit": 1048576,
                },
                {
                    "name": "models/gemini-2.5-flash-preview-tts",
                    "displayName": "TTS",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/lyria-3.5",
                    "displayName": "Lyria",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-embedding-001",
                    "displayName": "Embedding 001",
                    "supportedGenerationMethods": ["embedContent"],
                },
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = gemini_payload
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("valkyrie.providers.gemini.httpx.AsyncClient", return_value=mock_client):
            g_models = asyncio.run(GeminiProvider().fetch_models("AIza_test"))

        assert [m.id for m in g_models] == ["gemini-3.8-flash", "gemini-embedding-001"]
        assert ModelCapability.VISION in g_models[0].capabilities

        groq_payload = {
            "data": [
                {"id": "openai/gpt-oss-120b", "context_window": 131072, "active": True},
                {"id": "whisper-large-v3", "context_window": 448, "active": True},
                {"id": "canopylabs/orpheus-v1-english", "context_window": 4000, "active": True},
            ]
        }
        mock_resp.json.return_value = groq_payload
        with patch("valkyrie.providers.groq.httpx.AsyncClient", return_value=mock_client):
            q_models = asyncio.run(GroqProvider().fetch_models("gsk_test"))
        assert [m.id for m in q_models] == ["openai/gpt-oss-120b"]

    def test_flagship_ranking_and_resolve_model(self) -> None:
        m_old = ModelInfo(
            id="gemini-2.5-flash",
            name="Gemini 2.5 Flash",
            provider="gemini",
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE],
        )
        m_new = ModelInfo(
            id="gemini-3.8-flash",
            name="Gemini 3.8 Flash",
            provider="gemini",
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE],
        )
        reg = ModelRegistry(models={m_old.qualified_id: m_old, m_new.qualified_id: m_new})
        ordered = reg.list_models(provider="gemini")
        assert ordered[0].id == "gemini-3.8-flash"

        resolved, _ = reg.resolve_model("gemini-3.8-flash")
        assert resolved is not None
        assert resolved.qualified_id == "gemini/gemini-3.8-flash"


class TestModelRegistry:
    """Tests for unified registry caching and filtering."""

    def test_cache_roundtrip_and_filtering(self, tmp_path: Path) -> None:
        cache_file = tmp_path / "models.json"
        m1 = ModelInfo(
            id="llama-3.3-70b-versatile",
            name="Llama 3.3",
            provider="groq",
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE],
            context_window=131072,
        )
        m2 = ModelInfo(
            id="text-embedding-004",
            name="Embed 004",
            provider="gemini",
            capabilities=[ModelCapability.EMBEDDINGS],
            context_window=2048,
        )

        with patch("valkyrie.providers.registry.get_models_cache_path", return_value=cache_file):
            reg = ModelRegistry(models={m1.qualified_id: m1, m2.qualified_id: m2})
            reg.save_cache()

            loaded = ModelRegistry.load_cache()
            assert len(loaded.models) == 2
            assert len(loaded.list_models(provider="groq")) == 1
            assert len(loaded.list_models(role="embeddings")) == 1
            assert len(loaded.list_models(role="code")) == 1
            assert loaded.get_model("groq/llama-3.3-70b-versatile") is not None


class TestModelCli:
    """Tests for valkyrie model CLI commands."""

    def test_model_overview_and_set(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        cache_file = tmp_path / "models.json"

        m1 = ModelInfo(
            id="llama-3.3-70b-versatile",
            name="Llama 3.3",
            provider="groq",
            capabilities=[ModelCapability.CHAT, ModelCapability.CODE],
            context_window=131072,
        )
        m2 = ModelInfo(
            id="text-embedding-004",
            name="Embed 004",
            provider="gemini",
            capabilities=[ModelCapability.EMBEDDINGS],
            context_window=2048,
        )

        with (
            patch("valkyrie.core.config.get_config_path", return_value=config_file),
            patch("valkyrie.providers.registry.get_models_cache_path", return_value=cache_file),
        ):
            reg = ModelRegistry(models={m1.qualified_id: m1, m2.qualified_id: m2})
            reg.save_cache()

            runner = CliRunner()

            # List models
            res_list = runner.invoke(cli, ["model", "list"])
            assert res_list.exit_code == 0
            assert "groq/llama-3.3-70b-versatile" in res_list.output

            # List models filtered by provider
            res_filtered = runner.invoke(cli, ["model", "list", "--provider", "groq"])
            assert res_filtered.exit_code == 0
            assert "groq/llama-3.3-70b-versatile" in res_filtered.output
            assert "gemini/text-embedding-004" not in res_filtered.output

            # Set valid role (shorthand unique ID also works)
            res_set = runner.invoke(cli, ["model", "set", "code", "llama-3.3-70b-versatile"])
            assert res_set.exit_code == 0
            assert "Assigned" in res_set.output

            # Reject incompatible role
            res_bad = runner.invoke(
                cli, ["model", "set", "embeddings", "groq/llama-3.3-70b-versatile"]
            )
            assert res_bad.exit_code == 1
            assert "does not support role" in res_bad.output

            # Overview shows assignment
            res_overview = runner.invoke(cli, ["model"])
            assert res_overview.exit_code == 0
            assert "groq/llama-3.3-70b-versatile" in res_overview.output

            # Clear assignment
            res_clear = runner.invoke(cli, ["model", "set", "code", "unassigned"])
            assert res_clear.exit_code == 0
            assert "unassigned" in res_clear.output

"""Tests for the Phase 5 first-run setup wizard and top-level login/logout aliases."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from valkyria.cli.main import cli
from valkyria.core.config import ValkyriaConfig
from valkyria.providers.base import ModelCapability, ModelInfo

if TYPE_CHECKING:
    from pathlib import Path


def _mock_groq_provider() -> MagicMock:
    provider = MagicMock()
    provider.name = "Groq"
    provider.key = "groq"
    provider.validate_key = AsyncMock(return_value=True)
    provider.fetch_models = AsyncMock(
        return_value=[
            ModelInfo(
                id="llama-3.3-70b-versatile",
                name="Llama 3.3 70B",
                provider="groq",
                capabilities=[ModelCapability.CHAT, ModelCapability.CODE],
                context_window=131072,
            )
        ]
    )
    return provider


class TestSetupWizard:
    """Tests for valkyria setup."""

    def test_full_setup_wizard_local_mode(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        vault_file = tmp_path / "vault.enc"
        cache_file = tmp_path / "models.json"
        auth_file = tmp_path / "auth.json"

        mock_provider = _mock_groq_provider()

        # Sequence of prompts:
        # 1. Sign in with Google? n
        # 2. Master password + confirm: master1234, master1234
        # 3. Select provider: groq
        # 4. Groq API key: gsk_test_123456
        # 5. Connect another provider? n
        # 6. Preferred name: Anupam
        # 7. Profession: Developer
        # 8. Expertise level: advanced
        # 9. chat: 1, code: 0, planner: 0, summarization: 0 (vision skipped automatically)
        # 10. Embeddings mode: local
        # 11. Save this configuration? y
        inputs = "\n".join(
            [
                "n",
                "master1234",
                "master1234",
                "groq",
                "gsk_test_123456",
                "n",
                "Anupam",
                "Developer",
                "advanced",
                "1",
                "0",
                "0",
                "0",
                "pinecone",
                "y",
            ]
        ) + "\n"

        with (
            patch("valkyria.core.config.get_config_path", return_value=config_file),
            patch("valkyria.vault.store.get_vault_path", return_value=vault_file),
            patch("valkyria.providers.registry.get_models_cache_path", return_value=cache_file),
            patch("valkyria.auth.tokens.get_auth_path", return_value=auth_file),
            patch("valkyria.cli.setup_wizard.get_provider", return_value=mock_provider),
            patch("valkyria.providers.registry.get_provider", return_value=mock_provider),
            patch.dict(
                "valkyria.providers.registry.PROVIDERS",
                {"groq": mock_provider},
                clear=True,
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["setup"], input=inputs)

            assert result.exit_code == 0, result.output
            assert "Privacy Summary" in result.output
            assert "Configuration saved" in result.output

            cfg = ValkyriaConfig.load()
            assert cfg.first_run_complete is True
            assert cfg.profile.name == "Anupam"
            assert cfg.profile.profession == "Developer"
            assert cfg.profile.expertise == "advanced"
            assert cfg.models.chat == "groq/llama-3.3-70b-versatile"
            assert cfg.models.code is None
            assert cfg.embedding_mode == "pinecone"
            assert "groq" in cfg.providers

    def test_setup_cancel_on_review_does_not_save(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        vault_file = tmp_path / "vault.enc"
        cache_file = tmp_path / "models.json"
        auth_file = tmp_path / "auth.json"

        mock_provider = _mock_groq_provider()
        inputs = "\n".join(
            [
                "n",
                "master1234",
                "master1234",
                "groq",
                "gsk_test_123456",
                "n",
                "",
                "",
                "skip",
                "1",
                "0",
                "0",
                "0",
                "pinecone",
                "n",
            ]
        ) + "\n"

        with (
            patch("valkyria.core.config.get_config_path", return_value=config_file),
            patch("valkyria.vault.store.get_vault_path", return_value=vault_file),
            patch("valkyria.providers.registry.get_models_cache_path", return_value=cache_file),
            patch("valkyria.auth.tokens.get_auth_path", return_value=auth_file),
            patch("valkyria.cli.setup_wizard.get_provider", return_value=mock_provider),
            patch("valkyria.providers.registry.get_provider", return_value=mock_provider),
            patch.dict(
                "valkyria.providers.registry.PROVIDERS",
                {"groq": mock_provider},
                clear=True,
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ["setup"], input=inputs)

            assert result.exit_code == 0
            assert "Setup cancelled" in result.output
            assert not config_file.exists()

    def test_top_level_logout_alias(self, tmp_path: Path) -> None:
        auth_file = tmp_path / "auth.json"
        with patch("valkyria.auth.tokens.get_auth_path", return_value=auth_file):
            runner = CliRunner()
            result = runner.invoke(cli, ["logout"])
            assert result.exit_code == 0
            assert "Not signed in" in result.output

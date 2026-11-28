"""Global pytest fixtures — isolate config, cache, data dirs, and .env from live machine."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _isolated_valkyria_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep all test runs isolated from ~/.valkyria and the developer's .env."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg_config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg_data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg_cache"))
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("PINECONE_INDEX", raising=False)
    monkeypatch.setattr("valkyria.rag.embeddings._APP_ROOT", tmp_path / "app_root")
    monkeypatch.chdir(tmp_path)

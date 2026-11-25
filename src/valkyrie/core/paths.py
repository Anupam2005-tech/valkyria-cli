"""
Filesystem paths — config, data, and cache directories.

Everything lives under ~/.valkyrie/ by default. The XDG_CONFIG_HOME
and XDG_DATA_HOME environment variables are respected if set.
"""

import os
from pathlib import Path

_APP_DIR_NAME = ".valkyrie"


def get_config_dir() -> Path:
    """Return the config directory, creating it if needed."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) / "valkyrie" if xdg else Path.home() / _APP_DIR_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_data_dir() -> Path:
    """Return the data directory (sessions, indexes), creating it if needed."""
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) / "valkyrie" if xdg else get_config_dir() / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_cache_dir() -> Path:
    """Return the cache directory, creating it if needed."""
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) / "valkyrie" if xdg else get_config_dir() / "cache"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_vault_path() -> Path:
    """Return the path to the encrypted vault file."""
    return get_config_dir() / "vault.enc"


def get_auth_path() -> Path:
    """Return the path to the auth token file."""
    return get_config_dir() / "auth.json"


def get_config_path() -> Path:
    """Return the path to the main config file."""
    return get_config_dir() / "config.json"


def get_models_cache_path() -> Path:
    """Return the path to the cached provider model catalog."""
    return get_cache_dir() / "models.json"


def get_sessions_db_path() -> Path:
    """Return the path to the sessions database."""
    return get_data_dir() / "sessions.db"


def ensure_dirs() -> None:
    """Create all required directories."""
    get_config_dir()
    get_data_dir()
    get_cache_dir()


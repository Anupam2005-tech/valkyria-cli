"""
Vault store — manage encrypted API keys on disk.

The vault is a JSON dict of provider keys, encrypted as a single AES-256-GCM
blob and stored at ~/.valkyrie/vault.enc. The master password is never stored;
the user must enter it each session to unlock the vault.

Vault plaintext structure:
{
    "providers": {
        "groq": {"api_key": "gsk_...", "added_at": "2026-11-25T10:00:00"},
        "gemini": {"api_key": "AI...", "added_at": "2026-11-25T10:01:00"},
        "nvidia": {"api_key": "nvapi-...", "added_at": "2026-11-25T10:02:00"}
    },
    "updated_at": "2026-11-25T10:02:00"
}
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from valkyrie.core.paths import get_vault_path
from valkyrie.vault.crypto import decrypt, encrypt

# ── Supported providers ─────────────────────────────────────────────────────

SUPPORTED_PROVIDERS = {
    "groq": {
        "name": "Groq",
        "prefix": "gsk_",
        "url": "https://console.groq.com/keys",
        "description": "Fast inference for open models",
    },
    "gemini": {
        "name": "Google Gemini",
        "prefix": "AI",
        "url": "https://aistudio.google.com/apikey",
        "description": "Google's Gemini models",
    },
    "nvidia": {
        "name": "NVIDIA NIM",
        "prefix": "nvapi-",
        "url": "https://build.nvidia.com/",
        "description": "NVIDIA hosted inference",
    },
}

# Pinecone is configured via the application's .env, not user-supplied keys.
SERVICE_KEYS = dict(SUPPORTED_PROVIDERS)


def _empty_vault() -> dict[str, Any]:
    """Return an empty vault structure."""
    return {
        "providers": {},
        "updated_at": datetime.now(UTC).isoformat(),
    }


def vault_exists() -> bool:
    """Check if the vault file exists on disk."""
    return get_vault_path().exists()


def load_vault(password: str) -> dict[str, Any]:
    """
    Load and decrypt the vault.

    Args:
        password: The master password.

    Returns:
        Decrypted vault dict.

    Raises:
        FileNotFoundError: If the vault file doesn't exist.
        cryptography.exceptions.InvalidTag: If the password is wrong.
    """
    path = get_vault_path()
    if not path.exists():
        raise FileNotFoundError("No vault found. Run 'valkyrie keys add' to create one.")

    blob = path.read_bytes()
    plaintext = decrypt(blob, password)
    data: dict[str, Any] = json.loads(plaintext)
    return data


def save_vault(vault_data: dict[str, Any], password: str) -> None:
    """
    Encrypt and save the vault to disk.

    Args:
        vault_data: The vault dict to save.
        password: The master password.
    """
    vault_data["updated_at"] = datetime.now(UTC).isoformat()
    plaintext = json.dumps(vault_data, indent=2).encode("utf-8")
    blob = encrypt(plaintext, password)

    path = get_vault_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    path.chmod(0o600)


def add_key(password: str, provider: str, api_key: str) -> None:
    """
    Add or update an API key in the vault.

    Creates the vault if it doesn't exist.
    """
    vault = load_vault(password) if vault_exists() else _empty_vault()

    vault["providers"][provider] = {
        "api_key": api_key,
        "added_at": datetime.now(UTC).isoformat(),
    }

    save_vault(vault, password)


def remove_key(password: str, provider: str) -> bool:
    """
    Remove a provider key from the vault.

    Returns True if the key was found and removed, False if not found.
    """
    vault = load_vault(password)
    if provider not in vault["providers"]:
        return False

    del vault["providers"][provider]
    save_vault(vault, password)
    return True


def list_keys(password: str) -> dict[str, dict[str, str]]:
    """
    List all stored provider keys (masked).

    Returns:
        Dict of provider -> {masked_key, added_at}
    """
    if not vault_exists():
        return {}

    vault = load_vault(password)
    result: dict[str, dict[str, str]] = {}

    for provider, data in vault["providers"].items():
        key = data["api_key"]
        # Show first 4 and last 4 characters
        if len(key) > 12:
            masked = key[:4] + "·" * (len(key) - 8) + key[-4:]
        else:
            masked = key[:2] + "·" * max(len(key) - 2, 0)

        result[provider] = {
            "masked_key": masked,
            "added_at": data.get("added_at", "unknown"),
        }

    return result


def get_key(password: str, provider: str) -> str | None:
    """
    Get a decrypted API key for a provider.

    Returns the key string or None if not found.
    """
    if not vault_exists():
        return None

    vault = load_vault(password)
    provider_data = vault["providers"].get(provider)
    if provider_data is None:
        return None

    return str(provider_data["api_key"])


def get_vault_blob() -> bytes | None:
    """
    Get the raw encrypted vault blob for syncing.

    Returns the raw bytes or None if no vault exists.
    """
    path = get_vault_path()
    if not path.exists():
        return None
    return path.read_bytes()


def save_vault_blob(blob: bytes) -> None:
    """
    Save a raw encrypted vault blob (from sync).
    """
    path = get_vault_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    path.chmod(0o600)


"""
Vault module — encrypted key storage with Firebase sync.

Provides AES-256-GCM encrypted vault for API keys, with Argon2id KDF
and optional sync to Firebase Firestore as opaque blobs.
"""

from valkyria.vault.store import (
    SERVICE_KEYS,
    SUPPORTED_PROVIDERS,
    add_key,
    get_key,
    list_keys,
    remove_key,
    vault_exists,
)

__all__ = [
    "SERVICE_KEYS",
    "SUPPORTED_PROVIDERS",
    "add_key",
    "get_key",
    "list_keys",
    "remove_key",
    "vault_exists",
]

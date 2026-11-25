"""
Vault sync — push and pull the encrypted vault blob to/from Firebase Firestore.

The vault is synced as an opaque base64-encoded blob. Firebase never sees the
plaintext keys — only the encrypted binary. The user's Firebase UID is used
as the document path: users/{uid}/vault/keys

Conflict resolution: last-write-wins based on the updated_at timestamp
embedded in the encrypted payload. When pulling, if the local vault is newer,
we keep local; if remote is newer, we prompt before overwriting.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from valkyrie.auth.firebase_config import FIREBASE_CONFIG


# Firestore REST API base
_FIRESTORE_BASE = (
    f"https://firestore.googleapis.com/v1/"
    f"projects/{FIREBASE_CONFIG['projectId']}/"
    f"databases/filum/documents"
)


def _headers(id_token: str) -> dict[str, str]:
    """Auth headers for Firestore REST API."""
    return {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
    }


def push_vault(id_token: str, uid: str, vault_blob: bytes) -> bool:
    """
    Upload the encrypted vault blob to Firestore.

    Args:
        id_token: Valid Firebase ID token.
        uid: User's Firebase UID.
        vault_blob: Raw encrypted vault bytes.

    Returns:
        True on success, False on failure.
    """
    doc_path = f"users/{uid}/vault/keys"
    url = f"{_FIRESTORE_BASE}/{doc_path}"

    # Encode as base64 for Firestore bytesValue
    encoded = base64.b64encode(vault_blob).decode("ascii")

    payload: dict[str, Any] = {
        "fields": {
            "vault_blob": {"bytesValue": encoded},
            "updated_at": {
                "timestampValue": _now_iso(),
            },
        }
    }

    try:
        # Use PATCH to create or update the document
        response = httpx.patch(
            url,
            json=payload,
            headers=_headers(id_token),
            timeout=15.0,
        )
        return response.status_code in (200, 201)
    except httpx.HTTPError:
        return False


def pull_vault(id_token: str, uid: str) -> bytes | None:
    """
    Download the encrypted vault blob from Firestore.

    Args:
        id_token: Valid Firebase ID token.
        uid: User's Firebase UID.

    Returns:
        Raw encrypted vault bytes, or None if not found or error.
    """
    doc_path = f"users/{uid}/vault/keys"
    url = f"{_FIRESTORE_BASE}/{doc_path}"

    try:
        response = httpx.get(
            url,
            headers=_headers(id_token),
            timeout=15.0,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()

        blob_b64 = data.get("fields", {}).get("vault_blob", {}).get("bytesValue")
        if blob_b64 is None:
            return None

        return base64.b64decode(blob_b64)
    except (httpx.HTTPError, KeyError, ValueError):
        return None


def delete_remote_vault(id_token: str, uid: str) -> bool:
    """
    Delete the vault document from Firestore.

    Returns True on success.
    """
    doc_path = f"users/{uid}/vault/keys"
    url = f"{_FIRESTORE_BASE}/{doc_path}"

    try:
        response = httpx.delete(
            url,
            headers=_headers(id_token),
            timeout=15.0,
        )
        return response.status_code in (200, 204, 404)
    except httpx.HTTPError:
        return False


def _now_iso() -> str:
    """Current UTC time in ISO format for Firestore."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


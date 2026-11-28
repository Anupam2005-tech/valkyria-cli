"""
Token management — store, load, refresh Firebase auth tokens.

Tokens are stored in ~/.valkyria/auth.json. The refresh token is used
to obtain new ID tokens when they expire (Firebase ID tokens last 1 hour).
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

from valkyria.auth.firebase_config import (
    AUTH_API_BASE,
)
from valkyria.core.paths import get_auth_path

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class AuthUser:
    """Authenticated user info."""

    uid: str
    email: str
    display_name: str | None
    photo_url: str | None
    id_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp

    @property
    def is_expired(self) -> bool:
        """Check if the ID token has expired (with 5-minute buffer)."""
        return time.time() >= (self.expires_at - 300)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "uid": self.uid,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthUser:
        """Deserialize from dict."""
        return cls(
            uid=data["uid"],
            email=data["email"],
            display_name=data.get("display_name"),
            photo_url=data.get("photo_url"),
            id_token=data["id_token"],
            refresh_token=data["refresh_token"],
            expires_at=data.get("expires_at", 0),
        )

    @classmethod
    def from_oauth_callback(cls, data: dict[str, Any]) -> AuthUser:
        """Create from the OAuth callback data."""
        return cls(
            uid=data["uid"],
            email=data["email"],
            display_name=data.get("displayName"),
            photo_url=data.get("photoURL"),
            id_token=data["idToken"],
            refresh_token=data["refreshToken"],
            # Firebase ID tokens last 3600 seconds
            expires_at=time.time() + 3600,
        )


def save_auth(user: AuthUser) -> Path:
    """Save auth data to disk. Returns the file path."""
    path = get_auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix=".auth-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(json.dumps(user.to_dict(), indent=2) + "\n")
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return path


def load_auth() -> AuthUser | None:
    """Load auth data from disk. Returns None if not found."""
    path = get_auth_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return AuthUser.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def clear_auth() -> None:
    """Delete the auth file."""
    path = get_auth_path()
    if path.exists():
        path.unlink()


def refresh_id_token(user: AuthUser) -> AuthUser | None:
    """
    Refresh a session through the hosted authentication service.

    Returns updated AuthUser or None on failure.
    """
    url = f"{AUTH_API_BASE}/refresh"

    try:
        response = httpx.post(
            url,
            json={"refreshToken": user.refresh_token},
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()

        user.id_token = data["id_token"]
        user.refresh_token = data["refresh_token"]
        user.expires_at = time.time() + int(data.get("expires_in", 3600))
        save_auth(user)
        return user

    except (httpx.HTTPError, KeyError):
        return None


def get_valid_user() -> AuthUser | None:
    """
    Load auth and refresh if needed. Returns a user with a valid ID token,
    or None if not authenticated.
    """
    user = load_auth()
    if user is None:
        return None

    if user.is_expired:
        user = refresh_id_token(user)

    return user


def delete_firebase_account(id_token: str) -> tuple[bool, str]:
    """
    Permanently delete the Firebase Auth account through the hosted service.

    Returns (success, detail_message).
    """
    url = f"{AUTH_API_BASE}/delete"
    try:
        response = httpx.post(
            url,
            json={"idToken": id_token},
            timeout=15.0,
        )
        if response.status_code == 200:
            return True, "Account deleted from Firebase Authentication."

        detail = ""
        try:
            err_data = response.json()
            detail = str(err_data.get("error", ""))
        except ValueError:
            detail = response.text[:200]

        if detail == "CREDENTIAL_TOO_OLD_LOGIN_REQUIRED":
            return (
                False,
                "Firebase requires a recent sign-in before deleting an account. "
                "Run '/account switch' (or 'valkyria auth switch') to re-authenticate, "
                "then retry.",
            )
        return (
            False,
            f"Firebase account deletion failed ({response.status_code}): "
            f"{detail or 'unknown error'}",
        )
    except httpx.HTTPError as exc:
        return False, f"Network error during account deletion: {exc}"


"""
Vault cryptography — Argon2 key derivation + AES-256-GCM encryption.

The master password never touches disk. It is stretched with Argon2id into
a 256-bit key, which encrypts the vault payload with AES-256-GCM. Each
save generates a fresh random salt and nonce, so identical plaintext
produces different ciphertext.

Wire format (all big-endian):
    [2B version][16B salt][12B nonce][NB ciphertext+tag]
    version = 0x0001
"""

from __future__ import annotations

import os
import struct

import argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Constants ───────────────────────────────────────────────────────────────

VAULT_VERSION = 1
SALT_LENGTH = 16  # bytes
NONCE_LENGTH = 12  # bytes — standard for AES-GCM
KEY_LENGTH = 32  # bytes — AES-256
VERSION_HEADER = struct.Struct(">H")  # 2 bytes, big-endian unsigned short

# Argon2id parameters — tuned for interactive use on modern hardware
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MiB
ARGON2_PARALLELISM = 4


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit encryption key from a password using Argon2id.

    Args:
        password: The master password.
        salt: A 16-byte random salt.

    Returns:
        32-byte derived key.
    """
    raw = argon2.low_level.hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=KEY_LENGTH,
        type=argon2.low_level.Type.ID,
    )
    return raw


def encrypt(plaintext: bytes, password: str) -> bytes:
    """
    Encrypt plaintext with AES-256-GCM using a password-derived key.

    Returns the full wire-format blob (version + salt + nonce + ciphertext).
    """
    salt = os.urandom(SALT_LENGTH)
    nonce = os.urandom(NONCE_LENGTH)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    return VERSION_HEADER.pack(VAULT_VERSION) + salt + nonce + ciphertext


def decrypt(blob: bytes, password: str) -> bytes:
    """
    Decrypt a wire-format blob using the master password.

    Raises:
        ValueError: If the version is unsupported.
        cryptography.exceptions.InvalidTag: If the password is wrong
            or the data is corrupted.
    """
    # Parse header
    if len(blob) < VERSION_HEADER.size + SALT_LENGTH + NONCE_LENGTH + 16:
        raise ValueError("Vault data is too short or corrupted.")

    offset = 0
    (version,) = VERSION_HEADER.unpack_from(blob, offset)
    offset += VERSION_HEADER.size

    if version != VAULT_VERSION:
        raise ValueError(f"Unsupported vault version: {version}")

    salt = blob[offset : offset + SALT_LENGTH]
    offset += SALT_LENGTH

    nonce = blob[offset : offset + NONCE_LENGTH]
    offset += NONCE_LENGTH

    ciphertext = blob[offset:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def verify_password(blob: bytes, password: str) -> bool:
    """
    Check if a password can decrypt the vault blob.

    Returns True if the password is correct, False otherwise.
    """
    try:
        decrypt(blob, password)
        return True
    except Exception:
        return False


"""Tests for the vault crypto and store modules."""

import json
import os
import tempfile
from unittest.mock import patch

from valkyrie.vault.crypto import decrypt, derive_key, encrypt, verify_password


class TestVaultCrypto:
    """Tests for the cryptographic layer."""

    def test_derive_key_deterministic(self) -> None:
        """Same password + salt produces the same key."""
        salt = os.urandom(16)
        k1 = derive_key("testpassword", salt)
        k2 = derive_key("testpassword", salt)
        assert k1 == k2
        assert len(k1) == 32

    def test_derive_key_different_salts(self) -> None:
        """Different salts produce different keys."""
        k1 = derive_key("testpassword", os.urandom(16))
        k2 = derive_key("testpassword", os.urandom(16))
        assert k1 != k2

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Encrypt then decrypt returns original plaintext."""
        plaintext = b'{"providers": {"groq": {"api_key": "gsk_test123"}}}'
        password = "my-master-password"

        blob = encrypt(plaintext, password)
        result = decrypt(blob, password)
        assert result == plaintext

    def test_different_ciphertext_each_time(self) -> None:
        """Two encryptions of the same data produce different blobs (random salt+nonce)."""
        plaintext = b"same data"
        password = "password"
        blob1 = encrypt(plaintext, password)
        blob2 = encrypt(plaintext, password)
        assert blob1 != blob2

    def test_wrong_password_fails(self) -> None:
        """Decrypting with wrong password raises InvalidTag."""
        from cryptography.exceptions import InvalidTag

        plaintext = b"secret data"
        blob = encrypt(plaintext, "correct-password")

        try:
            decrypt(blob, "wrong-password")
            assert False, "Should have raised InvalidTag"
        except InvalidTag:
            pass

    def test_verify_password(self) -> None:
        """verify_password returns True for correct, False for wrong."""
        blob = encrypt(b"test", "correct")
        assert verify_password(blob, "correct") is True
        assert verify_password(blob, "wrong") is False

    def test_corrupted_blob_fails(self) -> None:
        """Corrupted data raises an error."""
        blob = encrypt(b"test", "password")
        corrupted = blob[:-5] + b"\x00" * 5
        assert verify_password(corrupted, "password") is False


class TestVaultStore:
    """Tests for the vault store operations."""

    def test_add_and_list_keys(self) -> None:
        """Add a key and list it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = os.path.join(tmpdir, "vault.enc")
            with patch("valkyrie.vault.store.get_vault_path", return_value=__import__("pathlib").Path(vault_path)):
                from valkyrie.vault.store import add_key, list_keys

                add_key("password123", "groq", "gsk_test_key_12345678")
                result = list_keys("password123")

                assert "groq" in result
                assert "gsk_" in result["groq"]["masked_key"]
                assert "5678" in result["groq"]["masked_key"]

    def test_add_and_get_key(self) -> None:
        """Add a key and retrieve the full value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = os.path.join(tmpdir, "vault.enc")
            with patch("valkyrie.vault.store.get_vault_path", return_value=__import__("pathlib").Path(vault_path)):
                from valkyrie.vault.store import add_key, get_key

                add_key("password123", "gemini", "AIzaSy_test_key")
                result = get_key("password123", "gemini")
                assert result == "AIzaSy_test_key"

    def test_remove_key(self) -> None:
        """Remove a key from the vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = os.path.join(tmpdir, "vault.enc")
            with patch("valkyrie.vault.store.get_vault_path", return_value=__import__("pathlib").Path(vault_path)):
                from valkyrie.vault.store import add_key, get_key, remove_key

                add_key("password123", "groq", "gsk_key")
                assert remove_key("password123", "groq") is True
                assert get_key("password123", "groq") is None

    def test_remove_nonexistent_key(self) -> None:
        """Removing a key that doesn't exist returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = os.path.join(tmpdir, "vault.enc")
            with patch("valkyrie.vault.store.get_vault_path", return_value=__import__("pathlib").Path(vault_path)):
                from valkyrie.vault.store import add_key, remove_key

                add_key("password123", "groq", "gsk_key")
                assert remove_key("password123", "nvidia") is False


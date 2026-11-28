"""Tests for account switching, Firebase account deletion, /account slash commands, and CLI."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from click.testing import CliRunner
from prompt_toolkit.document import Document

from valkyria.auth.account import _run_browser_oauth, delete_account, switch_account
from valkyria.auth.tokens import (
    AuthUser,
    delete_firebase_account,
    load_auth,
    refresh_id_token,
    save_auth,
)
from valkyria.chat.commands import ValkyriaCompleter
from valkyria.chat.engine import ChatEngine, _handle_slash_command, build_command_registry
from valkyria.cli.main import cli
from valkyria.core.config import ValkyriaConfig
from valkyria.core.paths import get_auth_path, get_config_path, get_vault_path
from valkyria.providers.registry import ModelRegistry

if TYPE_CHECKING:
    from pathlib import Path


def _sample_user(
    *,
    uid: str = "uid_alice",
    email: str = "alice@example.com",
    expires_offset: int = 3600,
) -> AuthUser:
    return AuthUser(
        uid=uid,
        email=email,
        display_name="Alice",
        photo_url=None,
        id_token="id_tok_alice",
        refresh_token="ref_tok_alice",
        expires_at=time.time() + expires_offset,
    )


class TestFirebaseAccountDeletionApi:
    """Unit tests for Firebase Identity Toolkit accounts:delete REST wrapper."""

    def test_delete_firebase_account_success(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        with patch("valkyria.auth.tokens.httpx.post", return_value=resp) as mock_post:
            ok, msg = delete_firebase_account("id_tok_123")

        assert ok is True
        assert "deleted" in msg.lower()
        assert mock_post.call_args.args[0].endswith("/api/auth/delete")
        assert mock_post.call_args.kwargs["json"] == {"idToken": "id_tok_123"}

    def test_delete_firebase_account_requires_recent_login(self) -> None:
        resp = MagicMock()
        resp.status_code = 400
        resp.json.return_value = {"error": "CREDENTIAL_TOO_OLD_LOGIN_REQUIRED"}
        with patch("valkyria.auth.tokens.httpx.post", return_value=resp):
            ok, msg = delete_firebase_account("stale_tok")

        assert ok is False
        assert "/account switch" in msg


def test_refresh_uses_hosted_endpoint() -> None:
    response = MagicMock()
    response.json.return_value = {
        "id_token": "new-id-token",
        "refresh_token": "new-refresh-token",
        "expires_in": "3600",
    }
    with patch("valkyria.auth.tokens.httpx.post", return_value=response) as mock_post:
        refreshed = refresh_id_token(_sample_user())

    assert refreshed is not None
    assert refreshed.id_token == "new-id-token"
    assert mock_post.call_args.args[0].endswith("/api/auth/refresh")
    assert mock_post.call_args.kwargs["json"] == {"refreshToken": "ref_tok_alice"}


def test_saved_auth_tokens_are_private() -> None:
    path = save_auth(_sample_user())
    assert path.stat().st_mode & 0o777 == 0o600


def test_browser_login_opens_after_listener_is_ready_with_one_time_state() -> None:
    opened_urls: list[str] = []

    def start_listener(**kwargs: object) -> None:
        on_ready = kwargs["on_ready"]
        assert callable(on_ready)
        on_ready()
        assert len(opened_urls) == 1
        params = parse_qs(urlsplit(opened_urls[0]).query)
        assert params["cli"] == ["1"]
        assert params["select_account"] == ["1"]
        assert params["state"] == [kwargs["expected_state"]]
        return None

    with (
        patch("valkyria.auth.account.AUTH_WEB_URL", "https://valkyria-cli.vercel.app/login"),
        patch("valkyria.auth.account.webbrowser.open", side_effect=opened_urls.append),
        patch("valkyria.auth.account.run_auth_server", side_effect=start_listener),
        patch("valkyria.auth.account.print_info") as printed_info,
    ):
        assert _run_browser_oauth(select_account=True) is None

    shown = " ".join(str(call.args[0]) for call in printed_info.call_args_list)
    assert "https://valkyria-cli.vercel.app/login" in shown
    assert "state=" not in shown


class TestAccountLifecycle:
    """Tests for switching accounts and deleting accounts cleanly."""

    def test_switch_account_keeps_existing_session_when_cancelled(self) -> None:
        save_auth(_sample_user())
        with (
            patch("valkyria.auth.account.webbrowser.open"),
            patch("valkyria.auth.account.run_auth_server", return_value=None),
        ):
            switched = switch_account(interactive=False)

        assert switched is None
        current = load_auth()
        assert current is not None
        assert current.email == "alice@example.com"

    def test_switch_account_updates_auth_and_pulls_remote_vault(self) -> None:
        save_auth(_sample_user())
        callback_data = {
            "uid": "uid_bob",
            "email": "bob@example.com",
            "displayName": "Bob",
            "photoURL": None,
            "idToken": "id_tok_bob",
            "refreshToken": "ref_tok_bob",
        }
        with (
            patch("valkyria.auth.account.webbrowser.open"),
            patch("valkyria.auth.account.run_auth_server", return_value=callback_data) as srv,
            patch("valkyria.auth.account.pull_vault", return_value=b"encrypted_bob_vault"),
            patch("valkyria.auth.account.click.confirm", return_value=True),
        ):
            switched = switch_account(interactive=True)

        assert srv.call_args.kwargs["select_account"] is True
        assert switched is not None
        assert switched.email == "bob@example.com"
        saved = load_auth()
        assert saved is not None and saved.uid == "uid_bob"
        assert get_vault_path().read_bytes() == b"encrypted_bob_vault"
        assert ValkyriaConfig.load().sync_enabled is True

    def test_delete_account_cleans_remote_and_local_state(self) -> None:
        save_auth(_sample_user())
        cfg = ValkyriaConfig(sync_enabled=True)
        cfg.save()
        get_vault_path().write_bytes(b"local_vault_bytes")

        with (
            patch("valkyria.auth.account.delete_remote_vault", return_value=True) as del_remote,
            patch(
                "valkyria.auth.account.delete_firebase_account",
                return_value=(True, "Account deleted."),
            ) as del_fb,
        ):
            ok = delete_account(assume_yes=True, purge_local=True)

        assert ok is True
        del_remote.assert_called_once_with("id_tok_alice", "uid_alice")
        del_fb.assert_called_once_with("id_tok_alice")
        assert not get_auth_path().exists()
        assert not get_vault_path().exists()
        assert get_config_path().exists()
        assert ValkyriaConfig.load().sync_enabled is False

    def test_delete_account_cancelled_preserves_auth(self) -> None:
        save_auth(_sample_user())
        with (
            patch("valkyria.auth.account.click.confirm", return_value=False),
            patch("valkyria.auth.account.delete_firebase_account") as del_fb,
        ):
            ok = delete_account(assume_yes=False)

        assert ok is False
        del_fb.assert_not_called()
        assert load_auth() is not None


class TestAccountSlashAndCli:
    """Tests for in-chat /account commands, /auth alias, autocomplete, and CLI commands."""

    def test_in_chat_account_switch_and_delete(self, tmp_path: Path) -> None:
        save_auth(_sample_user())
        engine = ChatEngine(
            config=ValkyriaConfig(),
            registry=ModelRegistry(),
            api_keys={"groq": "gsk_test"},
            initial_model="groq/llama-3.3-70b-versatile",
            workspace_root=tmp_path,
        )

        # Completer suggests /account and subcommands switch/delete
        completer = ValkyriaCompleter(build_command_registry(engine), tmp_path)
        cmd_names = [
            c.text for c in completer.get_completions(Document("/acc", cursor_position=4), None)
        ]
        assert "/account" in cmd_names
        subs = [
            c.text
            for c in completer.get_completions(Document("/account ", cursor_position=9), None)
        ]
        assert "switch" in subs
        assert "delete" in subs

        # /account status
        assert _handle_slash_command("/account status", engine) is True

        # /auth switch alias works
        callback_data = {
            "uid": "uid_carol",
            "email": "carol@example.com",
            "displayName": "Carol",
            "photoURL": None,
            "idToken": "id_tok_carol",
            "refreshToken": "ref_tok_carol",
        }
        with (
            patch("valkyria.auth.account.webbrowser.open"),
            patch("valkyria.auth.account.run_auth_server", return_value=callback_data),
            patch("valkyria.auth.account.pull_vault", return_value=None),
        ):
            assert _handle_slash_command("/acc sw", engine) is True

        cur = load_auth()
        assert cur is not None and cur.email == "carol@example.com"

        # /acc del --yes short alias works
        with (
            patch("valkyria.auth.account.delete_remote_vault", return_value=True),
            patch(
                "valkyria.auth.account.delete_firebase_account",
                return_value=(True, "Deleted"),
            ),
        ):
            assert _handle_slash_command("/acc del --yes", engine) is True

        assert load_auth() is None

    def test_cli_auth_switch_and_delete(self) -> None:
        save_auth(_sample_user())
        runner = CliRunner()

        callback_data = {
            "uid": "uid_dave",
            "email": "dave@example.com",
            "displayName": "Dave",
            "photoURL": None,
            "idToken": "id_tok_dave",
            "refreshToken": "ref_tok_dave",
        }
        with (
            patch("valkyria.auth.account.webbrowser.open"),
            patch("valkyria.auth.account.run_auth_server", return_value=callback_data),
            patch("valkyria.auth.account.pull_vault", return_value=None),
        ):
            res_sw = runner.invoke(cli, ["auth", "switch"])
        assert res_sw.exit_code == 0, res_sw.output
        assert "dave@example.com" in res_sw.output

        with (
            patch("valkyria.auth.account.delete_remote_vault", return_value=True),
            patch(
                "valkyria.auth.account.delete_firebase_account",
                return_value=(True, "Deleted"),
            ),
        ):
            res_del = runner.invoke(cli, ["auth", "delete", "--yes"])
        assert res_del.exit_code == 0, res_del.output
        assert "Deleted account" in res_del.output


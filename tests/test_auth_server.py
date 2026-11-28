"""Security checks for the browser-to-CLI authentication callback."""

from __future__ import annotations

import io
import json
from email.message import Message
from types import SimpleNamespace
from unittest.mock import Mock

from valkyria.auth import server as auth_server


def test_callback_requires_matching_origin_and_state() -> None:
    auth_server._result = auth_server._AuthResult()

    def post(origin: str, state: str) -> int:
        body = json.dumps(
            {
                "state": state,
                "idToken": "id-token",
                "refreshToken": "refresh-token",
                "uid": "user-id",
                "email": "user@example.com",
            }
        ).encode()
        headers = Message()
        headers["Origin"] = origin
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
        handler = object.__new__(auth_server._OAuthHandler)
        handler.path = "/callback"
        handler.headers = headers
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.server = SimpleNamespace(
            allowed_origin="https://valkyria-cli.vercel.app",
            expected_state="expected-state",
        )
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.do_POST()
        return handler.send_response.call_args.args[0]

    assert post("https://evil.example", "expected-state") == 403
    assert not auth_server._result.event.is_set()
    assert post("https://valkyria-cli.vercel.app", "wrong-state") == 403
    assert not auth_server._result.event.is_set()
    assert post("https://valkyria-cli.vercel.app", "expected-state") == 200
    assert auth_server._result.data is not None
    assert auth_server._result.data["uid"] == "user-id"

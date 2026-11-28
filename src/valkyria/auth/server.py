"""
Local OAuth server — receives the token callback from the hosted login page.

Spins up a minimal HTTP server on localhost to:
1. Bind to loopback before opening the browser
2. Receive a state-bound POST callback with Firebase tokens at /callback
3. Shut down after successful auth
"""

from __future__ import annotations

import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from valkyria.auth.firebase_config import (
    AUTH_WEB_URL,
    OAUTH_CALLBACK_HOST,
    OAUTH_CALLBACK_PATH,
    OAUTH_CALLBACK_PORT,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class _AuthResult:
    """Thread-safe container for the auth result."""

    def __init__(self) -> None:
        self.data: dict[str, Any] | None = None
        self.error: str | None = None
        self.event = threading.Event()


_result = _AuthResult()


class _OAuthHTTPServer(HTTPServer):
    """HTTPServer carrying per-run OAuth options."""

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        *,
        select_account: bool = False,
        expected_state: str,
    ) -> None:
        self.select_account = select_account
        self.expected_state = expected_state
        parts = urlsplit(AUTH_WEB_URL)
        self.allowed_origin = f"{parts.scheme}://{parts.netloc}"
        super().__init__(server_address, handler_class)


class _OAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for the local OAuth server."""

    server: _OAuthHTTPServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(404)
        self.end_headers()

    def _respond(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", self.server.allowed_origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok" if status == 200 else "error"}).encode())

    def do_POST(self) -> None:  # noqa: N802
        """Handle the token callback from the login page."""
        if self.path != OAUTH_CALLBACK_PATH:
            self._respond(404)
            return
        if self.headers.get("Origin") != self.server.allowed_origin:
            self._respond(403)
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            self._respond(415)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if not 0 < content_length <= 32768:
                self._respond(413)
                return
            data = json.loads(self.rfile.read(content_length))
            required = ("state", "idToken", "refreshToken", "uid", "email")
            if not isinstance(data, dict) or any(
                not isinstance(data.get(field), str) or not data[field]
                for field in required
            ):
                self._respond(400)
                return
            if not hmac.compare_digest(data["state"], self.server.expected_state):
                self._respond(403)
                return
        except (ValueError, UnicodeDecodeError):
            self._respond(400)
            return

        _result.data = data
        _result.event.set()
        self._respond(200)

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Handle CORS and Private Network Access preflight."""
        if (
            self.path != OAUTH_CALLBACK_PATH
            or self.headers.get("Origin") != self.server.allowed_origin
        ):
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", self.server.allowed_origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()


def run_auth_server(
    timeout: float = 300.0,
    *,
    select_account: bool = False,
    expected_state: str,
    on_ready: Callable[[], object],
) -> dict[str, Any] | None:
    """
    Start the local OAuth server, wait for auth, and return the result.

    Args:
        timeout: Seconds to wait for the user to complete sign-in.
        select_account: Whether to prompt Google's account chooser.
        expected_state: One-time state tied to this login attempt.
        on_ready: Opens the hosted page once the callback listener is ready.

    Returns:
        Dict with auth data (idToken, refreshToken, uid, email, etc.)
        or None if timed out or errored.
    """
    global _result
    _result = _AuthResult()

    server = _OAuthHTTPServer(
        (OAUTH_CALLBACK_HOST, OAUTH_CALLBACK_PORT),
        _OAuthHandler,
        select_account=select_account,
        expected_state=expected_state,
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        on_ready()
        # Wait for the callback
        _result.event.wait(timeout=timeout)
        return _result.data
    finally:
        server.shutdown()
        server_thread.join(timeout=2.0)


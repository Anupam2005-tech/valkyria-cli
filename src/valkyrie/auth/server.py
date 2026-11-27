"""
Local OAuth server — serves the login page and receives the token callback.

Spins up a minimal HTTP server on localhost to:
1. Serve the Google sign-in page at /
2. Receive the POST callback with Firebase tokens at /callback
3. Shut down after successful auth
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from valkyrie.auth.firebase_config import (
    OAUTH_CALLBACK_HOST,
    OAUTH_CALLBACK_PATH,
    OAUTH_CALLBACK_PORT,
)
from valkyrie.auth.login_page import get_login_page_html


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
    ) -> None:
        self.select_account = select_account
        super().__init__(server_address, handler_class)


class _OAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for the local OAuth server."""

    server: _OAuthHTTPServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:  # noqa: N802
        """Serve the login page."""
        if self.path == "/" or self.path == "/login":
            select_account = getattr(self.server, "select_account", False)
            html = get_login_page_html(select_account=select_account)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        """Handle the token callback from the login page."""
        if self.path == OAUTH_CALLBACK_PATH:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
                _result.data = data
                _result.event.set()

                # Send success response with CORS + PNA headers for the hosted login page
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Private-Network", "true")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())

            except (json.JSONDecodeError, KeyError) as e:
                _result.error = str(e)
                _result.event.set()
                self.send_response(400)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Private-Network", "true")
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Handle CORS and Private Network Access preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()


def run_auth_server(
    timeout: float = 300.0,
    *,
    select_account: bool = False,
) -> dict[str, Any] | None:
    """
    Start the local OAuth server, wait for auth, and return the result.

    Args:
        timeout: Seconds to wait for the user to complete sign-in.
        select_account: Whether to prompt Google's account chooser.

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
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        # Wait for the callback
        _result.event.wait(timeout=timeout)
        return _result.data
    finally:
        server.shutdown()
        server_thread.join(timeout=2.0)


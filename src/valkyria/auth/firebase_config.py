"""Public Firebase project identifiers and the hosted authentication URL."""

import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv()

# ── Firebase project: valkyria CLI (filum-708c0) ───────────────────────────

FIREBASE_CONFIG = {
    "authDomain": "filum-708c0.firebaseapp.com",
    "projectId": "filum-708c0",
    "storageBucket": "filum-708c0.firebasestorage.app",
    "messagingSenderId": "496089235861",
    "appId": "1:496089235861:web:c519aadaaf3e02203ab69c",
    "measurementId": "G-5XCHKRN258",
}

# Hosted web login page URL (override with VALKYRIA_AUTH_URL for local testing)
AUTH_WEB_URL = os.environ.get("VALKYRIA_AUTH_URL", "https://valkyria-cli.vercel.app/login")
_auth_web_parts = urlsplit(AUTH_WEB_URL)
AUTH_API_BASE = f"{_auth_web_parts.scheme}://{_auth_web_parts.netloc}/api/auth"

# Local OAuth callback server
OAUTH_CALLBACK_HOST = "127.0.0.1"
OAUTH_CALLBACK_PORT = 8085
OAUTH_CALLBACK_PATH = "/callback"


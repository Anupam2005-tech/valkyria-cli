"""
Firebase project configuration for Valkyrie CLI.

These are public-facing Firebase config values (safe to commit).
The Web API Key is NOT a secret — it identifies the Firebase project
for client-side auth calls, same as it would in a web app's HTML.
"""

# ── Firebase project: valkyria CLI (filum-708c0) ───────────────────────────

FIREBASE_CONFIG = {
    "apiKey": "REDACTED_FIREBASE_API_KEY",
    "authDomain": "filum-708c0.firebaseapp.com",
    "projectId": "filum-708c0",
    "storageBucket": "filum-708c0.firebasestorage.app",
    "messagingSenderId": "496089235861",
    "appId": "1:496089235861:web:f709d081fc867d9f3ab69c",
}

# Firebase Auth REST API (Identity Toolkit v1)
FIREBASE_AUTH_BASE = "https://identitytoolkit.googleapis.com/v1"
FIREBASE_TOKEN_BASE = "https://securetoken.googleapis.com/v1"

# Local OAuth callback server
OAUTH_CALLBACK_HOST = "127.0.0.1"
OAUTH_CALLBACK_PORT = 8085
OAUTH_CALLBACK_PATH = "/callback"


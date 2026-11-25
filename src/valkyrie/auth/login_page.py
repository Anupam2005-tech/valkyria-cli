"""
OAuth login page — served locally for Firebase Google sign-in.

This HTML page uses the Firebase JS SDK to trigger a Google popup sign-in,
then POSTs the resulting tokens back to the local callback server.
"""

from valkyrie.auth.firebase_config import (
    FIREBASE_CONFIG,
    OAUTH_CALLBACK_HOST,
    OAUTH_CALLBACK_PATH,
    OAUTH_CALLBACK_PORT,
)


def get_login_page_html(*, select_account: bool = False) -> str:
    """Return the HTML page that handles Google sign-in via Firebase JS SDK."""
    callback_url = (
        f"http://{OAUTH_CALLBACK_HOST}:{OAUTH_CALLBACK_PORT}{OAUTH_CALLBACK_PATH}"
    )
    subtitle_prompt = (
        "Choose a Google account to switch your workspace"
        if select_account
        else "Sign in to connect your workspace"
    )
    button_label = "CHOOSE GOOGLE ACCOUNT" if select_account else "SIGN IN WITH GOOGLE"
    custom_params_js = (
        "provider.setCustomParameters({ prompt: 'select_account' });"
        if select_account
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Valkyrie — Sign In</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .container {{
            text-align: center;
            max-width: 420px;
            padding: 48px 32px;
        }}
        .title {{
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 4px;
            color: #fff;
            margin-bottom: 8px;
        }}
        .subtitle {{
            font-size: 13px;
            color: #666;
            margin-bottom: 48px;
        }}
        .status {{
            font-size: 14px;
            color: #888;
            margin-bottom: 32px;
            min-height: 24px;
        }}
        .status.error {{ color: #e55; }}
        .status.success {{ color: #5e5; }}
        button {{
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            padding: 14px 32px;
            border: 1px solid #333;
            border-radius: 6px;
            background: #111;
            color: #fff;
            cursor: pointer;
            transition: all 0.15s ease;
            letter-spacing: 1px;
        }}
        button:hover {{ background: #1a1a1a; border-color: #0ff; color: #0ff; }}
        button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        .footer {{
            margin-top: 48px;
            font-size: 11px;
            color: #444;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">VALKYRIE</div>
        <div class="subtitle">Terminal-first AI workspace</div>
        <div class="status" id="status">{subtitle_prompt}</div>
        <button id="signin-btn" onclick="signIn()">{button_label}</button>
        <div class="footer">Authentication is handled by Firebase.<br>No passwords are stored locally.</div>
    </div>

    <script type="module">
        import {{ initializeApp }} from 'https://www.gstatic.com/firebasejs/11.8.1/firebase-app.js';
        import {{ getAuth, signInWithPopup, GoogleAuthProvider }} from 'https://www.gstatic.com/firebasejs/11.8.1/firebase-auth.js';

        const firebaseConfig = {{
            apiKey: "{FIREBASE_CONFIG['apiKey']}",
            authDomain: "{FIREBASE_CONFIG['authDomain']}",
            projectId: "{FIREBASE_CONFIG['projectId']}",
            storageBucket: "{FIREBASE_CONFIG['storageBucket']}",
            messagingSenderId: "{FIREBASE_CONFIG['messagingSenderId']}",
            appId: "{FIREBASE_CONFIG['appId']}"
        }};

        const app = initializeApp(firebaseConfig);
        const auth = getAuth(app);
        const provider = new GoogleAuthProvider();
        {custom_params_js}

        window.signIn = async function() {{
            const btn = document.getElementById('signin-btn');
            const status = document.getElementById('status');

            btn.disabled = true;
            status.className = 'status';
            status.textContent = 'Opening Google sign-in...';

            try {{
                const result = await signInWithPopup(auth, provider);
                const user = result.user;
                const idToken = await user.getIdToken();

                status.className = 'status success';
                status.textContent = 'Authenticated. Sending credentials to CLI...';

                const response = await fetch("{callback_url}", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{
                        idToken: idToken,
                        refreshToken: user.refreshToken,
                        uid: user.uid,
                        email: user.email,
                        displayName: user.displayName,
                        photoURL: user.photoURL,
                    }})
                }});

                if (response.ok) {{
                    status.textContent = 'Signed in as ' + user.email + '. You can close this tab.';
                    btn.style.display = 'none';
                    setTimeout(() => window.close(), 2000);
                }} else {{
                    throw new Error('CLI callback failed');
                }}
            }} catch (error) {{
                status.className = 'status error';
                if (error.code === 'auth/popup-closed-by-user') {{
                    status.textContent = 'Sign-in cancelled. Try again.';
                }} else if (error.code === 'auth/popup-blocked') {{
                    status.textContent = 'Popup blocked. Please allow popups and try again.';
                }} else {{
                    status.textContent = 'Error: ' + (error.message || error.code || 'unknown');
                }}
                btn.disabled = false;
            }}
        }};
    </script>
</body>
</html>"""


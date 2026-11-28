# Hosted CLI authentication

Set `FIREBASE_API_KEY` in the Vercel project's environment variables, then redeploy the site. Use the Firebase **Web API key** for the `filum-708c0` project. The same value is used by the hosted login page and the server routes for session refresh and account deletion. The Python package does not contain or require this key.

The Web API key is public by design: Firebase sign-in in a browser necessarily exposes it. Restrict it to Firebase-related APIs in Google Cloud. Do not use this key for other Google APIs, and never put a Firebase Admin service account, provider API key, or other private credential in `NEXT_PUBLIC_*`, `next.config.mjs`, or the package.

The CLI opens `https://valkyria-cli.vercel.app/login` with a one-time state value. The web page sends the signed-in user's tokens only to the matching loopback callback, and the CLI accepts callbacks only from the hosted page's origin with the matching state. Session refresh and account deletion go through the hosted `/api/auth` routes over HTTPS. For local development, set `VALKYRIA_AUTH_URL` to your local site's `/login` URL in the CLI environment.

Before distributing a new package, deploy the web changes and confirm the Vercel environment variable is present. Existing package versions call Firebase directly and do not use the new hosted routes.

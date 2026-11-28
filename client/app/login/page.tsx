"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertCircle, ArrowLeft, Check, Copy, Loader2, ShieldCheck, Terminal } from "lucide-react";
import Orb from "@/components/ui/orb";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import { Logo } from "@/components/ui/Logo";

const FIREBASE_CONFIG = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? "",
  authDomain: "filum-708c0.firebaseapp.com",
  projectId: "filum-708c0",
  storageBucket: "filum-708c0.firebasestorage.app",
  messagingSenderId: "496089235861",
  appId: "1:496089235861:web:f709d081fc867d9f3ab69c",
};

const LOCAL_CALLBACK_URL = "http://127.0.0.1:8085/callback";

type AuthState = "idle" | "loading" | "success" | "error";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47a5.54 5.54 0 0 1-2.4 3.63v3.02h3.88c2.27-2.09 3.54-5.17 3.54-8.89Z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.07 7.94-2.9l-3.88-3.02c-1.07.72-2.45 1.15-4.06 1.15-3.12 0-5.77-2.11-6.72-4.95H1.27v3.12A12 12 0 0 0 12 24Z"
      />
      <path
        fill="#FBBC05"
        d="M5.28 14.28A7.2 7.2 0 0 1 4.9 12c0-.79.14-1.56.38-2.28V6.6H1.27A12 12 0 0 0 0 12c0 1.93.46 3.76 1.27 5.4l4.01-3.12Z"
      />
      <path
        fill="#EA4335"
        d="M12 4.77c1.76 0 3.34.61 4.58 1.8l3.44-3.44C17.95 1.19 15.24 0 12 0A12 12 0 0 0 1.27 6.6l4.01 3.12c.95-2.84 3.6-4.95 6.72-4.95Z"
      />
    </svg>
  );
}

function LoginContent() {
  const searchParams = useSearchParams();
  const isCliFlow = searchParams.get("cli") === "1";
  const loginState = searchParams.get("state") ?? "";
  const selectAccount =
    searchParams.get("select_account") === "1" ||
    searchParams.get("select_account") === "true";

  const [status, setStatus] = useState<AuthState>("idle");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [copiedCmd, setCopiedCmd] = useState(false);

  if (!isCliFlow) {
    return (
      <main className="relative min-h-[100dvh] w-full overflow-hidden bg-[#101113] text-[#F2F4F1] flex items-center justify-center px-4 py-8">
        <div className="fixed inset-0 z-0 pointer-events-none">
          <Orb
            colors={["#FFC929", "#F2F4F1", "#1B1E24"]}
            backgroundColor="#101113"
            hoverIntensity={0.8}
            trail={1}
            glow={0.9}
            bleed={0.75}
            rotateOnHover
            followCursor
          />
        </div>
        <div className="relative z-10 w-full max-w-sm">
          <CardSpotlight
            color="#1D1F24"
            radius={320}
            className="p-6 sm:p-7 shadow-2xl shadow-black/60 border-[#2A2D33]"
          >
            <div className="flex items-center gap-3">
              <Logo size={28} />
              <div>
                <h1 className="text-lg font-semibold tracking-tight text-[#F2F4F1]">
                  Terminal sign-in only
                </h1>
                <p className="text-xs text-[#A2A8B0]">Valkyria CLI</p>
              </div>
            </div>

            <p className="mt-4 text-xs leading-relaxed text-[#A2A8B0]">
              Direct browser login is disabled. Run{" "}
              <code className="text-[#FFC929]">valkyria login</code> in your
              terminal to open an authenticated session.
            </p>

            <div className="mt-4 flex flex-col gap-2.5">
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard?.writeText("valkyria login");
                  setCopiedCmd(true);
                  setTimeout(() => setCopiedCmd(false), 1800);
                }}
                className="w-full inline-flex items-center justify-between rounded-lg border border-white/15 bg-[#101113] px-3.5 py-2.5 font-mono text-xs text-[#F2F4F1] transition hover:border-[#FFC929]/50"
              >
                <span className="inline-flex items-center gap-2">
                  <Terminal className="h-3.5 w-3.5 text-[#FFC929]" />
                  $ valkyria login
                </span>
                {copiedCmd ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Copy className="h-3.5 w-3.5 text-[#6F747A]" />
                )}
              </button>

              <Link
                href="/"
                className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg border border-[#26282C] bg-[#16181C]/80 px-4 py-2 text-xs font-medium text-[#A2A8B0] transition hover:text-[#F2F4F1] hover:border-[#3A3E45]"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Valkyria
              </Link>
            </div>
          </CardSpotlight>
        </div>
      </main>
    );
  }

  const handleGoogleSignIn = async () => {
    setStatus("loading");
    setStatusMessage("Opening Google sign-in...");

    try {
      if (!loginState || !/^[A-Za-z0-9_-]{32,128}$/.test(loginState)) {
        throw new Error("This login link is invalid. Run 'valkyria login' again.");
      }
      if (!FIREBASE_CONFIG.apiKey) {
        throw new Error("Sign-in is not configured. Please contact the site owner.");
      }
      const dynamicImport = new Function("u", "return import(u)") as (
        url: string
      ) => Promise<Record<string, unknown>>;

      const [firebaseAppMod, firebaseAuthMod] = await Promise.all([
        dynamicImport(
          "https://www.gstatic.com/firebasejs/11.8.1/firebase-app.js"
        ),
        dynamicImport(
          "https://www.gstatic.com/firebasejs/11.8.1/firebase-auth.js"
        ),
      ]);

      const initializeApp = firebaseAppMod.initializeApp as (
        cfg: typeof FIREBASE_CONFIG
      ) => unknown;
      const getApps = firebaseAppMod.getApps as () => unknown[];
      const getAuth = firebaseAuthMod.getAuth as (app: unknown) => unknown;
      const signInWithPopup = firebaseAuthMod.signInWithPopup as (
        auth: unknown,
        provider: unknown
      ) => Promise<{
        user: {
          uid: string;
          email: string | null;
          displayName: string | null;
          photoURL: string | null;
          refreshToken: string;
          getIdToken: () => Promise<string>;
        };
      }>;
      const GoogleAuthProvider = firebaseAuthMod.GoogleAuthProvider as {
        new (): {
          setCustomParameters: (params: Record<string, string>) => void;
        };
      };

      const apps = getApps();
      const app = apps.length > 0 ? apps[0] : initializeApp(FIREBASE_CONFIG);
      const auth = getAuth(app);
      const provider = new GoogleAuthProvider();
      if (selectAccount) {
        provider.setCustomParameters({ prompt: "select_account" });
      }

      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      const idToken = await user.getIdToken();

      setStatusMessage("Sending credentials to CLI...");

      const response = await fetch(LOCAL_CALLBACK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: loginState,
          idToken,
          refreshToken: user.refreshToken,
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
        }),
      });

      if (!response.ok) {
        throw new Error(`CLI callback failed (${response.status})`);
      }

      setStatus("success");
      setStatusMessage(
        `Signed in as ${user.email || "your account"}. Return to your terminal.`
      );
      setTimeout(() => {
        window.close();
      }, 2000);
    } catch (err: unknown) {
      const errorObj = err as { code?: string; message?: string };
      const code = errorObj?.code || "";
      let message = errorObj?.message || "Authentication failed.";

      if (code === "auth/popup-closed-by-user") {
        message = "Sign-in cancelled.";
      } else if (code === "auth/popup-blocked") {
        message = "Popup blocked. Allow popups and try again.";
      } else if (code === "auth/unauthorized-domain") {
        message =
          "Authorize valkyria-cli.vercel.app in Firebase Authentication settings.";
      } else if (
        message.includes("Failed to fetch") ||
        message.includes("NetworkError")
      ) {
        message = "CLI listener not reachable. Run 'valkyria login' in your terminal.";
      }

      setStatus("error");
      setStatusMessage(message);
    }
  };

  return (
    <main className="relative min-h-[100dvh] w-full overflow-hidden bg-[#101113] text-[#F2F4F1] flex items-center justify-center px-4 py-8">
      {/* Full-screen WebGL2 Orb backdrop */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <Orb
          colors={["#FFC929", "#F2F4F1", "#1B1E24"]}
          backgroundColor="#101113"
          hoverIntensity={1.1}
          trail={1}
          glow={1.15}
          bleed={0.85}
          rotateOnHover
          followCursor
        />
      </div>

      {/* Subtle radial vignette for contrast */}
      <div
        aria-hidden="true"
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(circle at center, rgba(16,17,19,0.22) 0%, rgba(16,17,19,0.82) 78%)",
        }}
      />

      {/* Compact CardSpotlight */}
      <div className="relative z-10 w-full max-w-sm">
        <CardSpotlight
          color="#1D1F24"
          radius={320}
          className="p-6 sm:p-7 shadow-2xl shadow-black/60 border-[#2A2D33]"
        >
          <div className="flex items-center gap-3">
            <Logo size={28} />
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-[#F2F4F1]">
                {status === "success"
                  ? "Connected"
                  : selectAccount
                    ? "Switch Valkyria account"
                    : "Sign in to Valkyria"}
              </h1>
              <p className="text-xs text-[#A2A8B0]">Terminal CLI</p>
            </div>
          </div>

          {statusMessage && (
            <div
              className={`mt-4 rounded-lg border px-3 py-2 text-xs flex items-start gap-2 ${
                status === "error"
                  ? "border-red-500/40 bg-red-500/10 text-red-200"
                  : status === "success"
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
                    : "border-[#FFC929]/30 bg-[#FFC929]/10 text-[#F2F4F1]"
              }`}
            >
              {status === "error" ? (
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-400" />
              ) : status === "success" ? (
                <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
              ) : (
                <Loader2 className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin text-[#FFC929]" />
              )}
              <span>{statusMessage}</span>
            </div>
          )}

          <div className="mt-5 flex flex-col gap-2.5">
            <button
              type="button"
              disabled={status === "loading" || status === "success"}
              onClick={handleGoogleSignIn}
              className="w-full inline-flex items-center justify-center gap-2.5 rounded-lg bg-[#F2F4F1] px-4 py-2.5 text-sm font-semibold text-[#101113] transition hover:bg-white disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {status === "loading" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Authorizing...
                </>
              ) : status === "success" ? (
                <>
                  <ShieldCheck className="h-4 w-4 text-emerald-700" />
                  Authorized
                </>
              ) : (
                <>
                  <GoogleIcon />
                  {selectAccount
                    ? "Choose Google account"
                    : "Continue with Google"}
                </>
              )}
            </button>

            <Link
              href="/"
              className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg border border-[#26282C] bg-[#16181C]/80 px-4 py-2 text-xs font-medium text-[#A2A8B0] transition hover:text-[#F2F4F1] hover:border-[#3A3E45]"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back
            </Link>
          </div>
        </CardSpotlight>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[100dvh] bg-[#101113] flex items-center justify-center text-[#A2A8B0] text-xs">
          Loading...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}

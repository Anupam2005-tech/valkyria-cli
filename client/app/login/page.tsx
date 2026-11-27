"use client";

import React, { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  KeyRound,
  Loader2,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import Orb from "@/components/ui/orb";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import {
  InterfaceCraftsCards,
  type CraftCardItem,
} from "@/components/ui/interface-crafts-cards";
import { Logo } from "@/components/ui/Logo";

const FIREBASE_CONFIG = {
  apiKey: "REDACTED_FIREBASE_API_KEY",
  authDomain: "filum-708c0.firebaseapp.com",
  projectId: "filum-708c0",
  storageBucket: "filum-708c0.firebasestorage.app",
  messagingSenderId: "496089235861",
  appId: "1:496089235861:web:f709d081fc867d9f3ab69c",
};

const AUTH_CRAFT_STEPS: CraftCardItem[] = [
  {
    num: "01",
    title: "Loopback Handshake",
    command: "valkyrie login",
    note: "CLI opens this page while listening on 127.0.0.1 for your token callback.",
  },
  {
    num: "02",
    title: "Firebase OAuth",
    command: "Google Sign-In",
    note: "Identity is verified with Firebase Auth — no passwords ever touch disk.",
  },
  {
    num: "03",
    title: "Vault Key Sync",
    command: "AES-256-GCM",
    note: "Your Groq, Gemini, and NVIDIA keys stay encrypted with Argon2id + AES-256-GCM.",
  },
  {
    num: "04",
    title: "Return to Terminal",
    command: "valkyrie chat",
    note: "Credentials stream directly to your waiting CLI session and close cleanly.",
  },
];

const AUTH_HIGHLIGHTS = [
  "Firebase Google OAuth with popup verification",
  "Client-side Argon2id + AES-256-GCM encrypted API vault",
  "Direct loopback handoff to your local CLI session",
];

type AuthState = "idle" | "loading" | "success" | "error";

function LoginContent() {
  const searchParams = useSearchParams();
  const rawPort = searchParams.get("port") || "8085";
  const rawHost = searchParams.get("host") || "127.0.0.1";
  const selectAccount =
    searchParams.get("select_account") === "1" ||
    searchParams.get("select_account") === "true";

  const safePort = useMemo(() => {
    const parsed = Number(rawPort);
    return Number.isInteger(parsed) && parsed >= 1 && parsed <= 65535
      ? String(parsed)
      : "8085";
  }, [rawPort]);

  const safeHost = useMemo(() => {
    return rawHost === "localhost" || rawHost === "127.0.0.1"
      ? rawHost
      : "127.0.0.1";
  }, [rawHost]);

  const callbackUrl = `http://${safeHost}:${safePort}/callback`;

  const [status, setStatus] = useState<AuthState>("idle");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [signedInEmail, setSignedInEmail] = useState<string>("");

  const handleGoogleSignIn = async () => {
    setStatus("loading");
    setStatusMessage("Opening Google sign-in popup...");

    try {
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

      setStatusMessage("Authenticated. Sending credentials to Valkyrie CLI...");

      const response = await fetch(callbackUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idToken,
          refreshToken: user.refreshToken,
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
        }),
      });

      if (!response.ok) {
        throw new Error(`CLI callback returned HTTP ${response.status}`);
      }

      setSignedInEmail(user.email || "your Google account");
      setStatus("success");
      setStatusMessage(
        `Signed in as ${user.email || "your account"}. You can return to your terminal.`
      );
      setTimeout(() => {
        window.close();
      }, 2000);
    } catch (err: unknown) {
      const errorObj = err as { code?: string; message?: string };
      const code = errorObj?.code || "";
      let message = errorObj?.message || "Authentication failed. Please try again.";

      if (code === "auth/popup-closed-by-user") {
        message = "Sign-in popup was closed before completing. Try again.";
      } else if (code === "auth/popup-blocked") {
        message = "Popup blocked by your browser. Allow popups and click Sign in again.";
      } else if (code === "auth/unauthorized-domain") {
        message =
          "Add valkyrie-cli.vercel.app to Firebase Console → Authentication → Settings → Authorized domains.";
      } else if (
        message.includes("Failed to fetch") ||
        message.includes("NetworkError")
      ) {
        message = `Could not reach your local CLI callback at ${safeHost}:${safePort}. Make sure 'valkyrie login' is running in your terminal.`;
      }

      setStatus("error");
      setStatusMessage(message);
    }
  };

  return (
    <main className="relative min-h-[100dvh] w-full overflow-x-hidden bg-[#101113] text-[#F2F4F1] flex flex-col items-center justify-center px-4 py-12">
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

      <div className="relative z-10 flex w-full max-w-5xl flex-col items-center gap-8">
        {/* Foreground CardSpotlight */}
        <div className="w-full max-w-md">
          <CardSpotlight
            color="#1D1F24"
            radius={360}
            className="shadow-2xl shadow-black/60 border-[#2A2D33]"
          >
            <div className="flex items-center justify-between gap-4 border-b border-[#26282C] pb-5">
              <div className="flex items-center gap-3">
                <Logo size={32} />
                <div>
                  <div className="font-tech text-xs tracking-[0.18em] uppercase text-[#F2F4F1]">
                    Valkyrie
                  </div>
                  <div className="font-mono text-[11px] text-[#A2A8B0]">
                    CLI Terminal Auth
                  </div>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[#FFC929]/30 bg-[#FFC929]/10 px-2.5 py-1 font-mono text-[11px] text-[#FFC929]">
                <Terminal className="h-3 w-3" />
                {safeHost}:{safePort}
              </span>
            </div>

            <div className="mt-6">
              <h1 className="font-display text-2xl font-bold tracking-tight text-[#F2F4F1]">
                {status === "success"
                  ? "Terminal session authorized"
                  : selectAccount
                    ? "Switch Valkyrie account"
                    : "Sign in to Valkyrie CLI"}
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-[#A2A8B0]">
                {status === "success"
                  ? `Connected as ${signedInEmail}. You can close this tab and return to your terminal.`
                  : "Authenticate with Google to unlock encrypted API key sync and connect your waiting CLI session."}
              </p>
            </div>

            <ul className="mt-5 space-y-2.5">
              {AUTH_HIGHLIGHTS.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-2.5 text-xs text-[#D5D8DC]"
                >
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#FFC929]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            {statusMessage && (
              <div
                className={`mt-5 rounded-lg border px-3.5 py-2.5 text-xs flex items-start gap-2 ${
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

            <div className="mt-6 flex flex-col gap-2.5">
              <button
                type="button"
                disabled={status === "loading" || status === "success"}
                onClick={handleGoogleSignIn}
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFC929] px-4 py-2.5 text-sm font-semibold text-[#101113] transition hover:bg-[#ffd557] disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {status === "loading" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Authorizing...
                  </>
                ) : status === "success" ? (
                  <>
                    <ShieldCheck className="h-4 w-4" />
                    Authorized — Return to Terminal
                  </>
                ) : (
                  <>
                    <KeyRound className="h-4 w-4" />
                    {selectAccount
                      ? "Choose Google Account"
                      : "Continue with Google"}
                  </>
                )}
              </button>

              <Link
                href="/"
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg border border-[#26282C] bg-[#16181C]/80 px-4 py-2 text-xs font-medium text-[#A2A8B0] transition hover:text-[#F2F4F1] hover:border-[#3A3E45]"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to Valkyrie overview
              </Link>
            </div>
          </CardSpotlight>
        </div>

        {/* Interactive Auth Flow Cards */}
        <InterfaceCraftsCards
          items={AUTH_CRAFT_STEPS}
          showCopy={false}
          className="w-full"
        />
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[100dvh] bg-[#101113] flex items-center justify-center text-[#A2A8B0] font-mono text-xs">
          Initializing Valkyrie Auth...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}

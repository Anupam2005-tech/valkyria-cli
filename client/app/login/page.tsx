"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, CheckCircle2, KeyRound, ShieldCheck, Terminal } from "lucide-react";
import Orb from "@/components/ui/orb";
import { CardSpotlight } from "@/components/ui/card-spotlight";
import { Logo } from "@/components/ui/Logo";

const AUTH_STEPS = [
  "Verify terminal loopback challenge & session nonce",
  "Authenticate identity via Firebase OAuth provider",
  "Derive local Argon2id + AES-256-GCM vault key",
  "Return encrypted token directly to Valkyrie CLI",
];

function LoginContent() {
  const searchParams = useSearchParams();
  const port = searchParams.get("port") || "48291";
  const state = searchParams.get("state") || "vk_cli_auth";
  const [authorized, setAuthorized] = useState(false);

  return (
    <main className="relative min-h-[100dvh] w-full overflow-hidden bg-[#101113] text-[#F2F4F1] flex flex-col items-center justify-center px-4 py-12">
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
            "radial-gradient(circle at center, rgba(16,17,19,0.22) 0%, rgba(16,17,19,0.78) 78%)",
        }}
      />

      {/* Foreground CardSpotlight */}
      <div className="relative z-10 w-full max-w-md">
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
              :{port}
            </span>
          </div>

          <div className="mt-6">
            <h1 className="font-display text-2xl font-bold tracking-tight text-[#F2F4F1]">
              {authorized ? "Terminal session authorized" : "Authorize Valkyrie CLI"}
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-[#A2A8B0]">
              {authorized
                ? "Your local CLI vault handshake is ready. You can return to your terminal window."
                : "A local `valkyrie login` session requested browser authentication to unlock your encrypted workspace."}
            </p>
          </div>

          <ul className="mt-5 space-y-2.5">
            {AUTH_STEPS.map((step) => (
              <li
                key={step}
                className="flex items-start gap-2.5 text-xs text-[#D5D8DC]"
              >
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#FFC929]" />
                <span>{step}</span>
              </li>
            ))}
          </ul>

          <div className="mt-6 rounded-lg border border-[#26282C] bg-[#0B0C0E]/90 px-3.5 py-2.5 font-mono text-xs text-[#A2A8B0] flex items-center justify-between">
            <span>session: {state.slice(0, 14)}</span>
            <span className="text-[#FFC929]">AES-256-GCM</span>
          </div>

          <div className="mt-6 flex flex-col gap-2.5">
            <button
              type="button"
              onClick={() => setAuthorized(true)}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFC929] px-4 py-2.5 text-sm font-semibold text-[#101113] transition hover:bg-[#ffd557]"
            >
              {authorized ? (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  Authorized — Return to Terminal
                </>
              ) : (
                <>
                  <KeyRound className="h-4 w-4" />
                  Continue & Authorize CLI
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


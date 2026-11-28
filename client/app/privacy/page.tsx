import type { Metadata } from "next";
import React from "react";
import { SiteHeader } from "@/components/ui/SiteHeader";
import { FooterSection } from "@/components/sections/FooterSection";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "How Valkyria CLI collects, uses, encrypts, and protects Google Sign-In data, client-side AES-256-GCM API key vaults, local JSON sessions, and Pinecone cloud RAG.",
  alternates: { canonical: "/privacy" },
};

interface PrivacySection {
  id: string;
  num: string;
  title: string;
  paragraphs: string[];
  bullets?: string[];
}

const PRIVACY_SECTIONS: PrivacySection[] = [
  {
    id: "overview",
    num: "01",
    title: "Overview & Scope",
    paragraphs: [
      "This Privacy Policy explains how Valkyria CLI (\"Valkyria\", \"we\", \"our\", or \"us\") and its companion web application at https://valkyria-cli.vercel.app collect, use, store, and protect information when you install or use the Valkyria command-line tool or authenticate with your Google account.",
      "Valkyria is designed around a local-first, bring-your-own-keys (BYOK) architecture. Your source code files, conversation transcripts, and decrypted provider API keys remain on your local machine.",
    ],
  },
  {
    id: "data-collected",
    num: "02",
    title: "Data We Collect (Including Google User Data)",
    paragraphs: [
      "We collect only the minimum information required to authenticate your CLI session and optionally synchronize your encrypted API key vault across devices:",
    ],
    bullets: [
      "Google Sign-In Account Data (via Firebase Authentication): When you run `valkyria login` in your terminal, you authenticate through Google OAuth (`openid`, `email`, and `profile` scopes). We receive your Google/Firebase unique user ID (UID), email address, display name, profile photo URL, and OAuth ID/refresh tokens.",
      "Optional Onboarding Profile: During CLI setup, you may optionally provide a preferred display name, profession, and expertise level. This is stored locally in your Valkyria configuration.",
      "Encrypted Key Vault Ciphertext: When vault sync is enabled, your third-party API keys (Groq, Google Gemini, NVIDIA) are encrypted client-side on your machine before upload. Cloud Firestore stores only the encrypted ciphertext, salt, and nonce—never plaintext keys.",
      "Session & Workspace Metadata: Your chat transcripts, checkpoints, and context history are stored locally as JSON files on your device (`~/.valkyria/data/sessions/` and `~/.valkyria/data/checkpoints/`).",
    ],
  },
  {
    id: "how-we-use",
    num: "03",
    title: "How We Use Your Data",
    paragraphs: [
      "We use the information described above strictly for the core functionality of Valkyria:",
    ],
    bullets: [
      "Authenticating your terminal CLI session via our local loopback OAuth callback (`127.0.0.1`) and maintaining login state across CLI commands (`valkyria auth status`, `/account switch`).",
      "Associating your client-side encrypted key vault ciphertext with your Firebase UID so you can restore your own encrypted vault on another workstation.",
      "Personalizing your local terminal greeting and tailoring assistant responses when optional profile fields are provided.",
      "We do NOT sell, rent, or lease your personal data or Google user data to third parties. We do NOT use your Google account data, source code, or prompts for advertising, profiling, or training AI models.",
    ],
  },
  {
    id: "google-limited-use",
    num: "04",
    title: "Google API Services User Data Policy (Limited Use)",
    paragraphs: [
      "Valkyria's use and transfer to any other application of information received from Google APIs strictly adheres to the Google API Services User Data Policy, including the Limited Use requirements.",
      "Specifically, Google user data obtained during sign-in (email address, display name, profile photo, and UID) is used solely to provide and maintain user-facing authentication and encrypted vault ownership within Valkyria. We never transfer Google user data to third parties except as necessary to operate authentication via Google Firebase, comply with applicable law, or protect against security abuse.",
    ],
  },
  {
    id: "local-vs-cloud",
    num: "05",
    title: "What Stays Local vs. Third-Party Processors",
    paragraphs: [
      "Valkyria separates local execution from external API calls so you always know what leaves your machine:",
    ],
    bullets: [
      "Local Machine Only: Workspace files, local JSON chat sessions, decrypted API keys, and your vault master password never leave your device in plaintext.",
      "AI Model Providers (Your Own Keys): When you send a chat turn or invoke an agent tool, only the relevant conversation turns and explicitly attached/retrieved context are sent directly from your machine to the provider you chose (Groq, Google Gemini, or NVIDIA NIM) under your own API keys.",
      "Pinecone Vector Store: When you run `/index`, workspace chunks are embedded and stored in your configured Pinecone index under a workspace namespace so `/search` and RAG can retrieve relevant code citations.",
      "Google Firebase (Auth & Firestore): Processes Google Sign-In authentication and stores only your UID, account metadata, and AES-256-GCM encrypted vault ciphertext.",
      "DuckDuckGo Search: When you run `/web` or the `web_search` tool, only your search query is sent to DuckDuckGo.",
    ],
  },
  {
    id: "security",
    num: "06",
    title: "Data Protection & Client-Side Encryption",
    paragraphs: [
      "All third-party API keys stored in Valkyria are encrypted on your machine before any network transfer using Argon2id key derivation and AES-256-GCM authenticated encryption derived from your master password.",
      "Because encryption occurs strictly client-side, neither Valkyria's maintainer nor Firebase can read or recover your API keys. All communication with Firebase, Pinecone, and model providers occurs over HTTPS/TLS, and the CLI OAuth callback listener binds exclusively to localhost (`127.0.0.1`).",
    ],
  },
  {
    id: "retention-deletion",
    num: "07",
    title: "Data Retention, Control & Deletion",
    paragraphs: [
      "We retain your Firebase authentication record and encrypted vault ciphertext only for as long as you maintain an active Valkyria account.",
      "You have full control over your data and can permanently delete it at any time:",
    ],
    bullets: [
      "In-App / CLI Deletion: Run `valkyria auth delete` in your terminal or `/account delete` inside chat. This permanently deletes your remote Firestore vault document, deletes your Firebase Authentication account, and removes local `auth.json` credentials.",
      "Revoking Google Access: You can revoke Valkyria's access to your Google account at any time via your Google Account Permissions settings (https://myaccount.google.com/permissions).",
      "Manual Deletion Requests: You may also request deletion of any account records by emailing abhowmik068@gmail.com from your registered email address.",
    ],
  },
  {
    id: "cookies-children",
    num: "08",
    title: "Cookies, Analytics & Children's Privacy",
    paragraphs: [
      "The Valkyria website does not use third-party advertising cookies, behavioral trackers, or cross-site analytics. During CLI-initiated Google Sign-In on `/login`, Firebase Authentication uses essential browser storage strictly to complete the OAuth handshake.",
      "Valkyria is a developer tool not directed at children under 13 (or the minimum age required in your jurisdiction), and we do not knowingly collect personal information from children.",
    ],
  },
  {
    id: "contact",
    num: "09",
    title: "Changes & Contact Information",
    paragraphs: [
      "We may update this Privacy Policy as Valkyria evolves (for example, when adding MCP server support or voice control). Any material updates will be reflected by updating the effective date at the top of this page.",
      "If you have any questions, security reports, or data deletion requests regarding this Privacy Policy or Valkyria's handling of Google user data, contact the maintainer directly at abhowmik068@gmail.com or via https://github.com/Anupam2005-tech/valkyria-cli.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#101113] text-[#F2F4F1] selection:bg-[#FFC929] selection:text-[#101113]">
      {/* Subtle architectural dot-grid */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.24]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(242, 244, 241, 0.14) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      <SiteHeader sectionLabel="/ privacy" />

      <main className="relative z-10 mx-auto max-w-[1380px] px-5 py-12 sm:px-8 sm:py-16">
        <div className="lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-12">
          {/* Left sticky index */}
          <aside className="hidden lg:block lg:self-start lg:sticky lg:top-20">
            <div className="py-2">
              <div className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.14em] text-[#6F747A]">
                Privacy Policy
              </div>
              <p className="mt-2 font-[family-name:var(--font-mono)] text-[11px] text-[#9499A0]">
                Effective: Nov 28, 2026
              </p>

              <ul className="mt-6 space-y-2 border-l border-white/[0.08] pl-3">
                {PRIVACY_SECTIONS.map((s) => (
                  <li key={s.id}>
                    <a
                      href={`#${s.id}`}
                      className="flex items-start gap-2 font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#FFC929]"
                    >
                      <span className="opacity-50">[{s.num}]</span>
                      <span className="leading-snug">{s.title}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </aside>

          {/* Right editorial legal content */}
          <article className="min-w-0 max-w-[76ch]">
            <div className="border-b border-white/[0.08] pb-8">
              <div className="font-[family-name:var(--font-mono)] text-xs text-[#FFC929]">
                Legal · Effective November 28, 2026
              </div>
              <h1 className="mt-2 text-[clamp(32px,4.5vw,48px)] font-semibold leading-[1.06] tracking-[-0.03em] text-[#F2F4F1]">
                Privacy{" "}
                <span className="font-[family-name:var(--font-accent)] font-normal italic text-[#FFC929]">
                  Policy.
                </span>
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-[#9499A0] sm:text-base">
                Clear disclosure of what Google user data and workspace data
                Valkyria accesses, how it is encrypted and used, and how you can
                delete it permanently.
              </p>
            </div>

            <div className="divide-y divide-white/[0.08]">
              {PRIVACY_SECTIONS.map((sec) => (
                <section key={sec.id} id={sec.id} className="scroll-mt-24 py-9">
                  <div className="flex items-baseline gap-3">
                    <span className="font-[family-name:var(--font-mono)] text-xs text-[#FFC929] tabular-nums">
                      [{sec.num}]
                    </span>
                    <h2 className="text-lg font-semibold tracking-tight text-[#F2F4F1] sm:text-xl">
                      {sec.title}
                    </h2>
                  </div>

                  <div className="mt-3 space-y-3">
                    {sec.paragraphs.map((p, idx) => (
                      <p
                        key={idx}
                        className="text-sm leading-[1.75] text-[#A3A7AB] sm:text-[15px]"
                      >
                        {p}
                      </p>
                    ))}
                  </div>

                  {sec.bullets && (
                    <ul className="mt-4 space-y-2.5 border-l border-white/[0.08] pl-4">
                      {sec.bullets.map((b, idx) => (
                        <li
                          key={idx}
                          className="text-sm leading-[1.7] text-[#A3A7AB]"
                        >
                          {b}
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              ))}
            </div>
          </article>
        </div>
      </main>

      <FooterSection />
    </div>
  );
}

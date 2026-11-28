import type { Metadata } from "next";
import React from "react";
import { SiteHeader } from "@/components/ui/SiteHeader";
import { FooterSection } from "@/components/sections/FooterSection";

export const metadata: Metadata = {
  title: "Terms & Conditions",
  description:
    "Terms and conditions for using Valkyria CLI, BYOK provider integrations, approval-gated system commands, and Firebase account sync.",
  alternates: { canonical: "/terms" },
};

const TERMS_SECTIONS = [
  {
    id: "acceptance",
    num: "01",
    title: "Acceptance of terms",
    body: "By installing or using the Valkyria CLI, or accessing https://valkyria-cli.vercel.app, you agree to be bound by these Terms & Conditions and our Privacy Policy.",
  },
  {
    id: "service",
    num: "02",
    title: "The service",
    body: "Valkyria provides an open-source, terminal-first AI coding agent, optional Firebase Google authentication, and client-side encrypted vault synchronization for user-supplied API keys.",
  },
  {
    id: "eligibility",
    num: "03",
    title: "Eligibility and accounts",
    body: "You must be legally able to enter a binding agreement in your jurisdiction and maintain accurate account information when signing in via `valkyria login`.",
  },
  {
    id: "byok",
    num: "04",
    title: "Bring-your-own-keys (BYOK)",
    body: "You supply your own API keys for Groq, Google Gemini, NVIDIA NIM, and Pinecone. You are solely responsible for provider billing, usage quotas, rate limits, and compliance with each provider's terms of service.",
  },
  {
    id: "acceptable-use",
    num: "05",
    title: "Acceptable use",
    body: "You agree not to use Valkyria for unlawful automation, unauthorized system access, malware distribution, or any activity that violates applicable law or third-party provider policies.",
  },
  {
    id: "ownership",
    num: "06",
    title: "User content and ownership",
    body: "You retain full ownership and intellectual property rights to your source code, prompts, local JSON sessions, indexed embeddings, and generated outputs.",
  },
  {
    id: "agent-actions",
    num: "07",
    title: "Agent actions & approval gates",
    body: "File edits, deletions, shell commands (`/run`), and package installations (`/pkg`) are gated behind interactive approval prompts unless you explicitly enable `/auto on`. You remain solely responsible for reviewing proposed diffs, commands, and maintaining backups or version control.",
  },
  {
    id: "third-party",
    num: "08",
    title: "Third-party services",
    body: "Valkyria integrates with Groq, Google Gemini, NVIDIA, Pinecone, DuckDuckGo, and Google Firebase. Your use of those external services is governed by their respective terms and privacy policies.",
  },
  {
    id: "liability",
    num: "09",
    title: "Disclaimers and limitation of liability",
    body: "Valkyria CLI is MIT-licensed software provided \"as is\" without warranties of any kind, express or implied. To the fullest extent permitted by applicable law, the maintainers shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the software.",
  },
  {
    id: "termination",
    num: "10",
    title: "Termination & account deletion",
    body: "You may stop using Valkyria and permanently delete your Firebase account and synced vault ciphertext at any time by running `/account delete` inside chat or `valkyria auth delete` in your terminal.",
  },
  {
    id: "changes",
    num: "11",
    title: "Changes to terms",
    body: "We may update these Terms & Conditions as the software evolves. Material changes will be reflected by updating the effective date on this page.",
  },
  {
    id: "contact",
    num: "12",
    title: "Governing principles & contact",
    body: "Questions or notices regarding these Terms & Conditions may be sent to abhowmik068@gmail.com or filed via https://github.com/Anupam2005-tech/valkyria-cli.",
  },
];

export default function TermsPage() {
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

      <SiteHeader sectionLabel="/ terms" />

      <main className="relative z-10 mx-auto max-w-[1380px] px-5 py-12 sm:px-8 sm:py-16">
        <div className="lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-12">
          {/* Left sticky index */}
          <aside className="hidden lg:block lg:self-start lg:sticky lg:top-20">
            <div className="py-2">
              <div className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.14em] text-[#6F747A]">
                Terms &amp; Conditions
              </div>
              <p className="mt-2 font-[family-name:var(--font-mono)] text-[11px] text-[#9499A0]">
                Effective: Nov 28, 2026
              </p>

              <ul className="mt-6 space-y-2 border-l border-white/[0.08] pl-3">
                {TERMS_SECTIONS.map((s) => (
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
                Terms &amp;{" "}
                <span className="font-[family-name:var(--font-accent)] font-normal italic text-[#FFC929]">
                  Conditions.
                </span>
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-[#9499A0] sm:text-base">
                Terms governing your use of the Valkyria CLI, bring-your-own-key
                model providers, approval-gated tools, and optional encrypted sync.
              </p>
            </div>

            <div className="divide-y divide-white/[0.08]">
              {TERMS_SECTIONS.map((sec) => (
                <section key={sec.id} id={sec.id} className="scroll-mt-24 py-9">
                  <div className="flex items-baseline gap-3">
                    <span className="font-[family-name:var(--font-mono)] text-xs text-[#FFC929] tabular-nums">
                      [{sec.num}]
                    </span>
                    <h2 className="text-lg font-semibold tracking-tight text-[#F2F4F1] sm:text-xl">
                      {sec.title}
                    </h2>
                  </div>
                  <p className="mt-3 text-sm leading-[1.75] text-[#A3A7AB] sm:text-[15px]">
                    {sec.body}
                  </p>
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

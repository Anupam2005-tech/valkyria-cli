import type { Metadata } from "next";
import React from "react";
import { Navbar } from "@/components/nav/Navbar";
import { FooterSection } from "@/components/sections/FooterSection";
import { DotGrid } from "@/components/ui/DotGrid";

export const metadata: Metadata = {
  title: "Terms & Conditions",
  description:
    "Terms and conditions for using Valkyrie CLI, BYOK provider integrations, approval-gated actions, and Firebase account sync.",
  alternates: { canonical: "/terms" },
};

const TERMS_SECTIONS = [
  {
    id: "acceptance",
    title: "1. Acceptance of terms",
    body: "By installing or using the Valkyrie CLI or visiting this website, you agree to these Terms & Conditions.",
  },
  {
    id: "service",
    title: "2. The service",
    body: "Valkyrie provides a local terminal-first AI agent CLI, optional Firebase authentication, and encrypted vault sync for user-supplied API keys.",
  },
  {
    id: "eligibility",
    title: "3. Eligibility and accounts",
    body: "You must be legally able to enter a binding agreement and provide accurate account details when authenticating.",
  },
  {
    id: "byok",
    title: "4. Bring-your-own-keys",
    body: "You supply your own API keys for Groq, Google Gemini, NVIDIA, and Pinecone. You are solely responsible for provider billing, rate limits, and compliance with each provider's terms.",
  },
  {
    id: "acceptable-use",
    title: "5. Acceptable use",
    body: "You agree not to use Valkyrie for unlawful automation, unauthorized system intrusion, or distribution of malicious payloads.",
  },
  {
    id: "ownership",
    title: "6. User content and ownership",
    body: "You retain all ownership rights to your source code, prompts, sessions, and generated outputs.",
  },
  {
    id: "agent-actions",
    title: "7. Agent actions",
    body: "File modifications and commands are gated behind approval prompts. You remain responsible for reviewing diffs and maintaining backups or version control.",
  },
  {
    id: "third-party",
    title: "8. Third-party services",
    body: "Valkyrie integrates with Groq, Google Gemini, NVIDIA, Pinecone, DuckDuckGo, and Firebase. Their respective terms govern your use of those services.",
  },
  {
    id: "liability",
    title: "9. Disclaimers and limitation of liability",
    body: "Valkyrie is provided 'as is' without warranties of any kind. To the fullest extent permitted by law, liability is excluded for indirect or consequential damages.",
  },
  {
    id: "termination",
    title: "10. Termination",
    body: "You may stop using Valkyrie and delete your account at any time via `/account delete` or `valkyrie auth delete`.",
  },
  {
    id: "changes",
    title: "11. Changes to terms",
    body: "We may update these terms from time to time and will update the 'Last updated' date below.",
  },
  {
    id: "governing-law",
    title: "12. Governing law and contact",
    body: "Governed by the laws of [jurisdiction]. Questions may be directed to [email].",
  },
];

export default function TermsPage() {
  return (
    <>
      <DotGrid dimmed />
      <Navbar solid />

      <main className="relative z-10 mx-auto max-w-[1280px] px-6 sm:px-10 pt-28 pb-24">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-12">
          <aside className="lg:col-span-4">
            <div className="lg:sticky lg:top-24">
              <span className="type-label text-[#FFC929]">Legal</span>
              <h1 className="type-display-lg mt-2 text-[#F2F4F1]">
                Terms &{" "}
                <span className="font-accent-word text-[#FFC929]">Conditions.</span>
              </h1>
              <p className="mt-3 font-mono text-xs text-[#9499A0]">
                Last updated: [2026-11-27]
              </p>
              <div className="mt-4 rounded-[12px] border border-[#FFC929]/35 bg-[#FFC929]/10 p-3 text-xs text-[#F2F4F1]">
                Draft. Have a qualified lawyer review before launch.
              </div>
              <ul className="mt-6 space-y-2 border-l border-[rgba(242,244,241,0.10)] pl-3">
                {TERMS_SECTIONS.map((s) => (
                  <li key={s.id}>
                    <a
                      href={`#${s.id}`}
                      className="text-xs text-[#A3A7AB] hover:text-[#FFC929] transition-colors"
                    >
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </aside>

          <article className="lg:col-span-8 max-w-[72ch] space-y-10">
            {TERMS_SECTIONS.map((s) => (
              <section key={s.id} id={s.id} className="scroll-mt-28">
                <h2 className="type-h3 text-[#F2F4F1]">{s.title}</h2>
                <p className="mt-3 text-[17px] leading-[1.7] text-[#A3A7AB]">
                  {s.body}
                </p>
              </section>
            ))}
          </article>
        </div>
      </main>

      <FooterSection />
    </>
  );
}


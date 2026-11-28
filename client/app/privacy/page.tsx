import type { Metadata } from "next";
import React from "react";
import { Navbar } from "@/components/nav/Navbar";
import { FooterSection } from "@/components/sections/FooterSection";
import { DotGrid } from "@/components/ui/DotGrid";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "How Valkyrie handles local SQLite sessions, client-side AES-256-GCM encrypted API keys, Firebase sync, and Pinecone cloud RAG.",
  alternates: { canonical: "/privacy" },
};

const PRIVACY_SECTIONS = [
  {
    id: "collect",
    title: "1. What we collect",
    body: "Account identifiers (email/UID via Firebase), profile details (display name, craft), session metadata, encrypted key vault ciphertext, and basic diagnostics [confirm].",
  },
  {
    id: "local",
    title: "2. What stays local",
    body: "Your workspace files, SQLite session transcripts, and decrypted API keys stay on your machine. Workspace RAG vectors are stored in your own Pinecone cloud index.",
  },
  {
    id: "providers",
    title: "3. What is sent to model providers",
    body: "Only the conversation turns and retrieved context needed for your request are sent to the model provider you selected (Groq, Gemini, or NVIDIA), under your own API keys.",
  },
  {
    id: "encryption",
    title: "4. How keys are protected",
    body: "Keys are encrypted client-side with Argon2id + AES-256-GCM using your master password. We cannot read your keys; losing your master password means synced ciphertext cannot be recovered.",
  },
  {
    id: "processors",
    title: "5. Firebase and other processors",
    body: "Firebase handles user authentication and stores encrypted vault ciphertext. Pinecone stores your workspace vector embeddings under your own Pinecone credentials.",
  },
  {
    id: "deletion",
    title: "6. Retention and deletion",
    body: "You can permanently delete your Firebase account and synced vault data anytime by running `/account delete` inside chat or `valkyrie auth delete` in your terminal.",
  },
  {
    id: "cookies",
    title: "7. Cookies and analytics",
    body: "[Decide: No third-party tracking cookies are used on this site. SessionStorage is used solely to remember the intro animation state.]",
  },
  {
    id: "security",
    title: "8. Children, security, international transfers",
    body: "Valkyrie is not directed at children under 13. Data processed by your chosen API providers is subject to their regional infrastructure.",
  },
  {
    id: "rights",
    title: "9. User rights and contact",
    body: "You may request access, export, or deletion of your account data at any time by contacting [email].",
  },
];

export default function PrivacyPage() {
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
                Privacy{" "}
                <span className="font-accent-word text-[#FFC929]">Policy.</span>
              </h1>
              <p className="mt-3 font-mono text-xs text-[#9499A0]">
                Last updated: [2026-11-27]
              </p>
              <div className="mt-4 rounded-[12px] border border-[#FFC929]/35 bg-[#FFC929]/10 p-3 text-xs text-[#F2F4F1]">
                Draft. Have a qualified lawyer review before launch.
              </div>
              <ul className="mt-6 space-y-2 border-l border-[rgba(242,244,241,0.10)] pl-3">
                {PRIVACY_SECTIONS.map((s) => (
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
            {PRIVACY_SECTIONS.map((s) => (
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


"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Check, Copy, Search, ChevronRight } from "lucide-react";
import { Navbar } from "@/components/nav/Navbar";
import { FooterSection } from "@/components/sections/FooterSection";
import { DotGrid } from "@/components/ui/DotGrid";
import { COMMANDS_REFERENCE } from "@/lib/constants";

interface DocSection {
  id: string;
  title: string;
  group: string;
  body: string;
  code?: { lang: string; content: string };
  callout?: { kind: "note" | "tip" | "warning"; text: string };
}

const DOC_SECTIONS: DocSection[] = [
  {
    id: "getting-started",
    title: "1. Getting started",
    group: "Start",
    body: "Valkyrie is a terminal-first AI coding agent that runs on your own Groq, Gemini and NVIDIA API keys. It pairs multi-provider streaming with Pinecone cloud RAG, SQLite session persistence, and explicit approval prompts before modifying files or running commands.",
    code: {
      lang: "bash",
      content: "pipx install valkyria-cli\nvalkyrie login\nvalkyrie chat",
    },
    callout: {
      kind: "tip",
      text: "Use the short binary alias `vk` anywhere instead of typing `valkyrie` (e.g. `vk chat`, `vk m rf`).",
    },
  },
  {
    id: "installation",
    title: "2. Installation",
    group: "Start",
    body: "Install Valkyrie in an isolated Python 3.12+ environment using pipx or uv. Ensure your Pinecone credentials (PINECONE_API_KEY and PINECONE_INDEX) are present in the application .env file.",
    code: {
      lang: "bash",
      content: "uv tool install valkyria-cli\n# or\npipx install valkyria-cli",
    },
  },
  {
    id: "login-and-onboarding",
    title: "3. Login and onboarding",
    group: "Start",
    body: "Run `valkyrie login` to authenticate via Firebase in your browser. Once signed in, the onboarding wizard collects your display name, craft, and provider API keys (Groq, Gemini, NVIDIA), encrypting them locally before any sync.",
    callout: {
      kind: "note",
      text: "Use `/account switch` (or `/acc sw`) inside chat to change Firebase accounts, or `/account delete` to permanently remove your account and synced ciphertext.",
    },
  },
  {
    id: "commands-reference",
    title: "4. Commands reference",
    group: "Reference",
    body: "Every workflow inside Valkyrie is accessible via slash commands. Below is the complete reference table.",
  },
  {
    id: "sessions-and-context",
    title: "5. Sessions and context",
    group: "Core",
    body: "Conversations are stored locally in SQLite. Use `/new` to open a clean context window while preserving your previous session, `/session` to resume or rename past threads, `/fork` to branch, `/compact` to summarize older turns, and `/context` to inspect token usage.",
    code: {
      lang: "text",
      content: "> /new refactor auth\nNew session started.\n> /compact 6",
    },
  },
  {
    id: "rag-and-indexing",
    title: "6. RAG and indexing",
    group: "Core",
    body: "Valkyrie chunks workspace files by type, generates embeddings, and upserts vectors exclusively into your Pinecone cloud index (never stored in a local vector DB). Run `/index .` to index your project and `/search` or automatic RAG injection to ground responses.",
    code: {
      lang: "bash",
      content: "valkyrie rag index .\nvalkyrie rag status",
    },
  },
  {
    id: "plan-and-build",
    title: "7. Plan and build",
    group: "Core",
    body: "Type `/plan <goal>` to break a task into inspectable steps before touching disk. Review, edit, and execute with `/build` while every file creation, edit, or deletion waits for confirmation.",
  },
  {
    id: "safety-and-permissions",
    title: "8. Safety and permissions",
    group: "Security",
    body: "Protected system paths (`/etc`, `/usr`, `/bin`, `.git`, `.env`, `vault.enc`, `auth.json`) are blocked from agent writes and deletes. Non-protected file changes display diffs and request `[Y/n/a]` approval unless you explicitly toggle `/auto on`.",
    callout: {
      kind: "warning",
      text: "Only enable `/auto on` inside trusted sandboxes or version-controlled workspaces.",
    },
  },
  {
    id: "providers-and-models",
    title: "9. Providers and models",
    group: "Core",
    body: "Switch providers or models on the fly with `/model <provider/id>`, `/model <provider>` to filter, or `/model pick` for an interactive selector. If a model is deprecated (such as retired Gemini models), Valkyrie surfaces instant one-command replacements.",
    code: {
      lang: "text",
      content: "> /model gemini\n> /model gemini/gemini-3.8-flash",
    },
  },
  {
    id: "vault-and-key-sync",
    title: "10. Vault and key sync",
    group: "Security",
    body: "API keys are derived with Argon2id and encrypted client-side using AES-256-GCM before ever touching Firebase. Only ciphertext leaves your machine.",
  },
  {
    id: "troubleshooting",
    title: "11. Troubleshooting",
    group: "Help",
    body: "If Firebase sign-in fails with `auth/unauthorized-domain`, verify `localhost` and `127.0.0.1` are listed under Authorized Domains in Firebase Console. If RAG reports a missing key, confirm `PINECONE_API_KEY` is set in `.env`.",
  },
  {
    id: "faq",
    title: "12. FAQ",
    group: "Help",
    body: "Visit the FAQ section on the home page for quick answers on pricing, supported operating systems, and offline vs. cloud boundaries.",
  },
];

function CodeBlock({ lang, content }: { lang: string; content: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(content);
    } catch {
      // ignore
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="my-5 overflow-hidden rounded-[12px] border border-[rgba(242,244,241,0.12)] bg-[#101113]">
      <div className="flex items-center justify-between border-b border-[rgba(242,244,241,0.10)] px-4 py-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-[#9499A0]">
          {lang}
        </span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#A3A7AB] hover:text-[#FFC929] transition-colors"
        >
          {copied ? <Check className="h-3 w-3 text-[#FFC929]" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-xs sm:text-sm leading-relaxed text-[#F2F4F1]">
        <code>{content}</code>
      </pre>
    </div>
  );
}

export default function DocsPage() {
  const [activeId, setActiveId] = useState("getting-started");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      } else if (e.key === "Escape") {
        setPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    const onScroll = () => {
      for (const sec of DOC_SECTIONS) {
        const el = document.getElementById(sec.id);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.top <= 160 && r.bottom >= 120) {
          setActiveId(sec.id);
          break;
        }
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const filteredSections = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return DOC_SECTIONS;
    return DOC_SECTIONS.filter(
      (s) => s.title.toLowerCase().includes(q) || s.body.toLowerCase().includes(q)
    );
  }, [query]);

  const groups = ["Start", "Core", "Security", "Reference", "Help"];

  const activeIdx = DOC_SECTIONS.findIndex((s) => s.id === activeId);
  const prevSec = activeIdx > 0 ? DOC_SECTIONS[activeIdx - 1] : null;
  const nextSec = activeIdx < DOC_SECTIONS.length - 1 ? DOC_SECTIONS[activeIdx + 1] : null;

  return (
    <>
      <DotGrid dimmed />
      <Navbar solid />

      <main className="relative z-10 mx-auto max-w-[1280px] px-6 sm:px-10 pt-28 pb-24">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
          {/* Left Sidebar */}
          <aside className="lg:col-span-3">
            <div className="lg:sticky lg:top-24 space-y-5">
              <button
                type="button"
                onClick={() => setPaletteOpen(true)}
                className="flex w-full items-center justify-between rounded-[12px] border border-[rgba(242,244,241,0.14)] bg-[#151619] px-3.5 py-2.5 text-xs text-[#A3A7AB] hover:border-[#FFC929]/50 transition-colors min-h-[44px]"
              >
                <span className="inline-flex items-center gap-2">
                  <Search className="h-3.5 w-3.5" strokeWidth={1.5} />
                  Search docs...
                </span>
                <kbd className="rounded bg-[#26282C] px-1.5 py-0.5 font-mono text-[10px] text-[#F2F4F1]">
                  Ctrl K
                </kbd>
              </button>

              <nav aria-label="Documentation sections" className="space-y-4">
                {groups.map((grp) => {
                  const items = DOC_SECTIONS.filter((s) => s.group === grp);
                  const collapsed = collapsedGroups[grp];
                  return (
                    <div key={grp}>
                      <button
                        type="button"
                        onClick={() =>
                          setCollapsedGroups((p) => ({ ...p, [grp]: !p[grp] }))
                        }
                        className="flex w-full items-center justify-between py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-[#9499A0] hover:text-[#F2F4F1]"
                      >
                        <span>{grp}</span>
                        <ChevronRight
                          className={`h-3.5 w-3.5 transition-transform ${
                            collapsed ? "" : "rotate-90"
                          }`}
                        />
                      </button>
                      {!collapsed && (
                        <ul className="mt-1.5 space-y-1 border-l border-[rgba(242,244,241,0.10)] pl-3">
                          {items.map((item) => {
                            const active = activeId === item.id;
                            return (
                              <li key={item.id}>
                                <a
                                  href={`#${item.id}`}
                                  onClick={() => setActiveId(item.id)}
                                  className={`block py-1 text-sm transition-colors ${
                                    active
                                      ? "font-medium text-[#FFC929]"
                                      : "text-[#A3A7AB] hover:text-[#F2F4F1]"
                                  }`}
                                >
                                  {item.title}
                                </a>
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* Center Content */}
          <article className="lg:col-span-6 max-w-[72ch]">
            <span className="type-label text-[#FFC929]">Documentation</span>
            <h1 className="type-display-lg mt-2 text-[#F2F4F1]">
              User{" "}
              <span className="font-accent-word text-[#FFC929]">manual.</span>
            </h1>

            <div className="mt-10 space-y-14">
              {DOC_SECTIONS.map((sec) => (
                <section key={sec.id} id={sec.id} className="scroll-mt-28">
                  <h2 className="type-h3 text-[#F2F4F1]">{sec.title}</h2>
                  <p className="mt-3 text-[17px] leading-[1.7] text-[#A3A7AB]">
                    {sec.body}
                  </p>

                  {sec.code && <CodeBlock lang={sec.code.lang} content={sec.code.content} />}

                  {sec.callout && (
                    <div
                      className={`my-5 rounded-[12px] border p-4 text-sm leading-relaxed ${
                        sec.callout.kind === "warning"
                          ? "border-[#E06D53]/40 bg-[#E06D53]/10 text-[#F2F4F1]"
                          : sec.callout.kind === "tip"
                          ? "border-[#FFC929]/40 bg-[#FFC929]/10 text-[#F2F4F1]"
                          : "border-[rgba(242,244,241,0.18)] bg-[#151619] text-[#A3A7AB]"
                      }`}
                    >
                      <span className="mr-2 font-mono text-xs uppercase tracking-wider text-[#FFC929]">
                        {sec.callout.kind}:
                      </span>
                      {sec.callout.text}
                    </div>
                  )}

                  {sec.id === "commands-reference" && (
                    <div className="mt-6 overflow-x-auto rounded-[16px] border border-[rgba(242,244,241,0.12)] bg-[#151619]">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="border-b border-[rgba(242,244,241,0.10)] font-mono text-xs uppercase tracking-wider text-[#9499A0]">
                            <th className="px-4 py-3">Command</th>
                            <th className="px-4 py-3">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {COMMANDS_REFERENCE.map((row) => (
                            <tr
                              key={row.cmd}
                              className="border-b border-[rgba(242,244,241,0.08)] last:border-b-0"
                            >
                              <td className="px-4 py-2.5 font-mono text-xs text-[#FFC929] whitespace-nowrap">
                                {row.cmd}
                              </td>
                              <td className="px-4 py-2.5 text-[#A3A7AB]">{row.action}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              ))}
            </div>

            {/* Prev / Next + Edit link */}
            <div className="mt-16 flex flex-wrap items-center justify-between gap-4 border-t border-[rgba(242,244,241,0.10)] pt-8">
              <div className="flex items-center gap-4">
                {prevSec && (
                  <a
                    href={`#${prevSec.id}`}
                    className="rounded-full border border-[rgba(242,244,241,0.14)] px-4 py-2 text-xs text-[#A3A7AB] hover:text-[#F2F4F1]"
                  >
                    Prev: {prevSec.title}
                  </a>
                )}
                {nextSec && (
                  <a
                    href={`#${nextSec.id}`}
                    className="rounded-full border border-[rgba(242,244,241,0.14)] px-4 py-2 text-xs text-[#A3A7AB] hover:text-[#FFC929]"
                  >
                    Next: {nextSec.title}
                  </a>
                )}
              </div>
              <Link
                href="/"
                className="font-mono text-xs text-[#9499A0] hover:text-[#FFC929]"
              >
                Edit this page [link]
              </Link>
            </div>
          </article>

          {/* Right TOC */}
          <aside className="hidden lg:block lg:col-span-3">
            <div className="sticky top-24">
              <span className="type-label text-[#9499A0]">On this page</span>
              <ul className="mt-4 space-y-2 border-l border-[rgba(242,244,241,0.10)] pl-3">
                {DOC_SECTIONS.map((sec) => (
                  <li key={sec.id}>
                    <a
                      href={`#${sec.id}`}
                      className={`block text-xs transition-colors ${
                        activeId === sec.id
                          ? "text-[#FFC929] font-medium"
                          : "text-[#9499A0] hover:text-[#F2F4F1]"
                      }`}
                    >
                      {sec.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </main>

      {/* Command Palette Modal */}
      {paletteOpen && (
        <div
          className="fixed inset-0 z-[80] flex items-start justify-center bg-black/70 px-4 pt-24 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setPaletteOpen(false);
          }}
        >
          <div className="w-full max-w-lg rounded-[20px] border border-[rgba(242,244,241,0.18)] bg-[#151619] p-4 shadow-soft">
            <div className="flex items-center gap-3 border-b border-[rgba(242,244,241,0.10)] pb-3">
              <Search className="h-4 w-4 text-[#FFC929]" />
              <input
                autoFocus
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Jump to a manual section..."
                className="w-full bg-transparent text-sm text-[#F2F4F1] placeholder-[#9499A0] focus:outline-none"
              />
            </div>
            <ul className="mt-3 max-h-72 overflow-y-auto space-y-1">
              {filteredSections.map((s) => (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    onClick={() => {
                      setActiveId(s.id);
                      setPaletteOpen(false);
                    }}
                    className="flex items-center justify-between rounded-[10px] px-3 py-2 text-sm text-[#A3A7AB] hover:bg-[#26282C] hover:text-[#FFC929]"
                  >
                    <span>{s.title}</span>
                    <span className="font-mono text-[11px] text-[#9499A0]">{s.group}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <FooterSection />
    </>
  );
}


"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronRight,
  Copy,
  Github,
  Menu,
  Search,
  X,
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { FooterSection } from "@/components/sections/FooterSection";
import { COMMANDS_REFERENCE } from "@/lib/constants";

interface DocSection {
  id: string;
  num: string;
  title: string;
  group: string;
  body: string;
  code?: { lang: string; content: string };
  callout?: { kind: "note" | "tip" | "warning"; text: string };
}

const DOC_SECTIONS: DocSection[] = [
  {
    id: "getting-started",
    num: "01",
    title: "Getting started",
    group: "Start",
    body: "Valkyria is a terminal-first AI coding agent that runs on your own Groq, Gemini, and NVIDIA API keys. It pairs multi-provider streaming with Pinecone cloud RAG, sandboxed command & package tools, JSON session persistence, and explicit approval prompts before touching your machine.",
    code: {
      lang: "bash",
      content: "pipx install valkyria-cli\nvalkyria login\nvalkyria chat",
    },
    callout: {
      kind: "tip",
      text: "Use the short binary alias `vk` anywhere instead of typing `valkyria` (e.g. `vk chat`, `vk m rf`).",
    },
  },
  {
    id: "installation",
    num: "02",
    title: "Installation",
    group: "Start",
    body: "Install Valkyria in an isolated Python 3.12+ environment using pipx or uv. Sign-in opens the hosted browser page; the CLI does not need a Firebase API key. Configure Pinecone only if you enable cloud retrieval.",
    code: {
      lang: "bash",
      content: "uv tool install valkyria-cli\n# or\npipx install valkyria-cli",
    },
  },
  {
    id: "login-and-onboarding",
    num: "03",
    title: "Login and onboarding",
    group: "Start",
    body: "Run `valkyria login` in your terminal to open the protected browser sign-in flow. Once authenticated, the onboarding wizard collects your display name, craft, and provider API keys (Groq, Gemini, NVIDIA), encrypting them locally with AES-256-GCM before any sync.",
    callout: {
      kind: "note",
      text: "Use `/account switch` (or `/acc sw`) inside chat to change Firebase accounts, or `/account delete` to permanently remove your account and synced ciphertext.",
    },
  },
  {
    id: "terminal-and-packages",
    num: "04",
    title: "Terminal commands & packages",
    group: "Core",
    body: "Valkyria can run shell commands (`run_command` / `/run`) and manage packages (`pkg_install` / `/pkg`) across pip, pip3, uv, pipx, npm, yarn, pnpm, cargo, brew, apt, and dnf. Every execution is locked to your workspace root, checked against a destructive command denylist, and gated by `[Y/n/a]` approval.",
    code: {
      lang: "text",
      content: "> /run pytest -q\n> /pkg pip install httpx\n> /pkg npm install lucide-react",
    },
  },
  {
    id: "commands-reference",
    num: "05",
    title: "Commands reference",
    group: "Reference",
    body: "Every workflow inside Valkyria is accessible via slash commands. Below is the complete reference table.",
  },
  {
    id: "sessions-and-context",
    num: "06",
    title: "Sessions and context",
    group: "Core",
    body: "Conversations are stored locally as JSON files in `~/.valkyria/data/sessions/` (with LangGraph checkpoints in `~/.valkyria/data/checkpoints/`). Use `/new` to open a clean context window while preserving your previous session, `/session` to resume or rename past threads, `/fork` to branch, `/compact` to summarize older turns, and `/budget` to inspect token usage.",
    code: {
      lang: "text",
      content: "> /new refactor auth\nNew session started.\n> /compact 6",
    },
  },
  {
    id: "rag-and-indexing",
    num: "07",
    title: "RAG and indexing",
    group: "Core",
    body: "Valkyria chunks workspace files by type, generates embeddings, and upserts vectors into your Pinecone cloud index. Run `/index .` to index your project and `/search` or automatic RAG injection to ground responses with file citations.",
    code: {
      lang: "bash",
      content: "valkyria rag index .\nvalkyria rag status",
    },
  },
  {
    id: "safety-and-permissions",
    num: "08",
    title: "Safety and permissions",
    group: "Security",
    body: "Protected system paths (`/etc`, `/usr`, `/bin`, `.git`, `.env`, `vault.enc`, `auth.json`) are blocked from agent reads/writes, and destructive shell patterns (e.g. `rm -rf /`, `dd of=/dev/...`, fork bombs) are hard-blocked before prompting. Non-protected changes preview diffs and request `[Y/n/a]` approval unless `/auto on` is toggled.",
    callout: {
      kind: "warning",
      text: "Only enable `/auto on` inside trusted sandboxes or version-controlled workspaces.",
    },
  },
  {
    id: "providers-and-models",
    num: "09",
    title: "Providers and models",
    group: "Core",
    body: "Switch providers or models on the fly with `/model <provider/id>`, `/model <provider>` to filter, or `/model pick` for an interactive selector. If a model is deprecated, Valkyria surfaces instant one-command replacements without silent substitutions.",
    code: {
      lang: "text",
      content: "> /model gemini\n> /model groq/llama-3.3-70b-versatile",
    },
  },
  {
    id: "vault-and-key-sync",
    num: "10",
    title: "Vault and key sync",
    group: "Security",
    body: "API keys are derived with Argon2id and encrypted client-side using AES-256-GCM before ever touching Firebase. Only ciphertext leaves your machine.",
  },
  {
    id: "troubleshooting",
    num: "11",
    title: "Troubleshooting",
    group: "Help",
    body: "If Firebase sign-in fails with `auth/unauthorized-domain`, verify your deployment domain and `127.0.0.1` are listed under Authorized Domains in Firebase Console. If `/login` shows 'Terminal sign-in only', launch it from `valkyria login` in your terminal rather than opening `/login` directly.",
  },
];

const GITHUB_URL = "https://github.com/Anupam2005-tech/valkyria-cli";

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
    <div className="my-5 overflow-hidden border border-white/[0.09] bg-[#0D0E10]">
      <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-2">
        <span className="font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.12em] text-[#6F747A]">
          {lang}
        </span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 font-[family-name:var(--font-mono)] text-[11px] text-[#9499A0] transition-colors hover:text-[#FFC929]"
        >
          {copied ? (
            <Check className="h-3 w-3 text-[#FFC929]" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-[family-name:var(--font-mono)] text-xs leading-relaxed text-[#E5E7EB] sm:text-sm">
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    const elements = DOC_SECTIONS.map((s) => document.getElementById(s.id)).filter(
      (el): el is HTMLElement => el !== null
    );
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      { rootMargin: "-18% 0px -65% 0px", threshold: 0 }
    );
    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
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

      {/* OpenCode-style minimal sticky header */}
      <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#101113]/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1380px] items-center justify-between px-5 sm:px-8">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2.5 text-[#F2F4F1] transition-opacity hover:opacity-90"
            >
              <Logo size={24} />
              <span className="font-[family-name:var(--font-mono)] text-sm font-semibold tracking-tight">
                valkyria
              </span>
            </Link>
            <span className="hidden font-[family-name:var(--font-mono)] text-xs text-[#6F747A] sm:inline">
              / docs
            </span>
          </div>

          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/"
              className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
            >
              Overview
            </Link>
            <Link
              href="/#changelog"
              className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
            >
              Changelog
            </Link>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              aria-label="Valkyria on GitHub"
              className="text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
            >
              <Github className="h-4 w-4" />
            </a>
            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              className="inline-flex items-center gap-2 border border-white/20 px-3 py-1 font-[family-name:var(--font-mono)] text-xs text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
            >
              <Search className="h-3 w-3" />
              <span>Ctrl K</span>
            </button>
          </nav>

          <button
            type="button"
            onClick={() => setMobileMenuOpen((v) => !v)}
            aria-label="Toggle documentation menu"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/10 text-[#F2F4F1] md:hidden"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="border-t border-white/[0.07] bg-[#101113] px-5 py-4 md:hidden">
            <div className="flex flex-col gap-2.5">
              {DOC_SECTIONS.map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  onClick={() => {
                    setActiveId(s.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`flex items-center gap-2.5 font-[family-name:var(--font-mono)] text-xs ${
                    activeId === s.id ? "text-[#FFC929]" : "text-[#9499A0]"
                  }`}
                >
                  <span className="opacity-60">[{s.num}]</span>
                  <span>{s.title}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main 3-column OpenCode editorial docs layout */}
      <div className="relative z-10 mx-auto max-w-[1380px] px-5 sm:px-8">
        <div className="py-10 lg:grid lg:grid-cols-[200px_minmax(0,1fr)_200px] lg:gap-12">
          {/* Left Sticky Sidebar */}
          <aside className="hidden lg:block lg:self-start lg:sticky lg:top-20">
            <div className="space-y-6 py-2">
              <button
                type="button"
                onClick={() => setPaletteOpen(true)}
                className="flex w-full items-center justify-between border border-white/[0.10] bg-[#141518] px-3 py-2 font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:border-[#FFC929]/50 hover:text-[#F2F4F1]"
              >
                <span className="inline-flex items-center gap-2">
                  <Search className="h-3.5 w-3.5" />
                  Search...
                </span>
                <kbd className="text-[10px] text-[#6F747A]">⌘K</kbd>
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
                        className="flex w-full items-center justify-between py-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.14em] text-[#6F747A] hover:text-[#F2F4F1]"
                      >
                        <span>{grp}</span>
                        <ChevronRight
                          className={`h-3 w-3 transition-transform ${
                            collapsed ? "" : "rotate-90"
                          }`}
                        />
                      </button>
                      {!collapsed && (
                        <ul className="mt-1.5 space-y-1.5">
                          {items.map((item) => {
                            const active = activeId === item.id;
                            return (
                              <li key={item.id}>
                                <a
                                  href={`#${item.id}`}
                                  onClick={() => setActiveId(item.id)}
                                  className={`flex items-center gap-2 font-[family-name:var(--font-mono)] text-xs transition-colors ${
                                    active
                                      ? "text-[#FFC929]"
                                      : "text-[#9499A0] hover:text-[#F2F4F1]"
                                  }`}
                                >
                                  <span className="opacity-50">[{item.num}]</span>
                                  <span className="truncate">{item.title}</span>
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

          {/* Center Documentation Content */}
          <main className="min-w-0 max-w-[74ch]">
            <div className="border-b border-white/[0.08] pb-8">
              <div className="font-[family-name:var(--font-mono)] text-xs text-[#FFC929]">
                Manual · v0.1.3
              </div>
              <h1 className="mt-2 text-[clamp(32px,4.5vw,48px)] font-semibold leading-[1.06] tracking-[-0.03em] text-[#F2F4F1]">
                Valkyria{" "}
                <span className="font-[family-name:var(--font-accent)] font-normal italic text-[#FFC929]">
                  documentation.
                </span>
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-[#9499A0] sm:text-base">
                Installation, slash commands, sandboxed shell &amp; package tools,
                Pinecone cloud RAG, and client-side key encryption.
              </p>
            </div>

            <div className="divide-y divide-white/[0.08]">
              {DOC_SECTIONS.map((sec) => (
                <section key={sec.id} id={sec.id} className="scroll-mt-24 py-10">
                  <div className="flex items-baseline gap-3">
                    <span className="font-[family-name:var(--font-mono)] text-xs text-[#FFC929] tabular-nums">
                      [{sec.num}]
                    </span>
                    <h2 className="text-xl font-semibold tracking-tight text-[#F2F4F1]">
                      {sec.title}
                    </h2>
                  </div>

                  <p className="mt-3 text-sm leading-[1.75] text-[#A3A7AB] sm:text-[15px]">
                    {sec.body}
                  </p>

                  {sec.code && <CodeBlock lang={sec.code.lang} content={sec.code.content} />}

                  {sec.callout && (
                    <div
                      className={`my-5 border p-4 text-xs leading-relaxed sm:text-sm ${
                        sec.callout.kind === "warning"
                          ? "border-[#E06D53]/40 bg-[#E06D53]/10 text-[#F2F4F1]"
                          : sec.callout.kind === "tip"
                          ? "border-[#FFC929]/35 bg-[#FFC929]/10 text-[#F2F4F1]"
                          : "border-white/[0.12] bg-[#141518] text-[#A3A7AB]"
                      }`}
                    >
                      <span className="mr-2 font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-wider text-[#FFC929]">
                        {sec.callout.kind}:
                      </span>
                      {sec.callout.text}
                    </div>
                  )}

                  {sec.id === "commands-reference" && (
                    <div className="mt-6 overflow-x-auto border border-white/[0.09] bg-[#141518]">
                      <table className="w-full text-left text-xs sm:text-sm">
                        <thead>
                          <tr className="border-b border-white/[0.08] bg-[#101113] font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-wider text-[#6F747A]">
                            <th className="px-4 py-3">Command</th>
                            <th className="px-4 py-3">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.06]">
                          {COMMANDS_REFERENCE.map((row) => (
                            <tr key={row.cmd} className="hover:bg-white/[0.02]">
                              <td className="whitespace-nowrap px-4 py-2.5 font-[family-name:var(--font-mono)] text-xs text-[#FFC929]">
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

            {/* Prev / Next Navigation */}
            <div className="flex flex-wrap items-center justify-between gap-4 border-t border-white/[0.08] pt-8">
              <div>
                {prevSec && (
                  <a
                    href={`#${prevSec.id}`}
                    className="inline-flex items-center gap-2 border border-white/20 px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs text-[#A3A7AB] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    <span>{prevSec.title}</span>
                  </a>
                )}
              </div>
              <div>
                {nextSec && (
                  <a
                    href={`#${nextSec.id}`}
                    className="inline-flex items-center gap-2 border border-white/20 px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                  >
                    <span>{nextSec.title}</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
            </div>
          </main>

          {/* Right Sticky TOC */}
          <aside className="hidden lg:block lg:self-start lg:sticky lg:top-20">
            <div className="py-2">
              <div className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.14em] text-[#6F747A]">
                On this page
              </div>
              <ul className="mt-4 space-y-2 border-l border-white/[0.08] pl-3">
                {DOC_SECTIONS.map((sec) => (
                  <li key={sec.id}>
                    <a
                      href={`#${sec.id}`}
                      onClick={() => setActiveId(sec.id)}
                      className={`block font-[family-name:var(--font-mono)] text-xs transition-colors ${
                        activeId === sec.id
                          ? "text-[#FFC929]"
                          : "text-[#6F747A] hover:text-[#F2F4F1]"
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
      </div>

      {/* Command Palette Modal */}
      {paletteOpen && (
        <div
          className="fixed inset-0 z-[80] flex items-start justify-center bg-black/75 px-4 pt-24 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setPaletteOpen(false);
          }}
        >
          <div className="w-full max-w-lg border border-white/15 bg-[#141518] p-4 shadow-2xl">
            <div className="flex items-center gap-3 border-b border-white/[0.08] pb-3">
              <Search className="h-4 w-4 text-[#FFC929]" />
              <input
                autoFocus
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Jump to a manual section..."
                className="w-full bg-transparent font-[family-name:var(--font-mono)] text-xs text-[#F2F4F1] placeholder-[#6F747A] focus:outline-none sm:text-sm"
              />
            </div>
            <ul className="mt-3 max-h-72 space-y-1 overflow-y-auto">
              {filteredSections.map((s) => (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    onClick={() => {
                      setActiveId(s.id);
                      setPaletteOpen(false);
                    }}
                    className="flex items-center justify-between px-3 py-2 text-xs text-[#A3A7AB] transition hover:bg-white/[0.05] hover:text-[#FFC929]"
                  >
                    <span>
                      <span className="mr-2 font-[family-name:var(--font-mono)] opacity-50">
                        [{s.num}]
                      </span>
                      {s.title}
                    </span>
                    <span className="font-[family-name:var(--font-mono)] text-[10px] text-[#6F747A]">
                      {s.group}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <FooterSection />
    </div>
  );
}

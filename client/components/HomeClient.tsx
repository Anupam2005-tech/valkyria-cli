"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Copy,
  Github,
  Menu,
  Mic,
  Plug,
  Shield,
  Smartphone,
  Terminal,
  X,
} from "lucide-react";
import { BrandLogo } from "@/components/ui/BrandLogos";
import { Logo } from "@/components/ui/Logo";
import { Timeline } from "@/components/ui/timeline";
import { VALKYRIA_TIMELINE_DATA } from "@/components/timeline-demo";
import { FooterSection } from "@/components/sections/FooterSection";
import {
  COMPARISON_ROWS,
  FAQ_ITEMS,
  HOW_IT_WORKS_STEPS,
} from "@/lib/constants";

const RAIL_SECTIONS = [
  { id: "overview", num: "1", label: "Overview" },
  { id: "capabilities", num: "2", label: "Capabilities" },
  { id: "flight-path", num: "3", label: "Flight path" },
  { id: "get-started", num: "4", label: "Get started" },
  { id: "coming-soon", num: "5", label: "Coming soon" },
  { id: "stack", num: "6", label: "Stack & diff" },
  { id: "changelog", num: "7", label: "Changelog" },
  { id: "faq", num: "8", label: "Questions" },
  { id: "open-source", num: "9", label: "Open source" },
] as const;

const HERO_CMD_SAMPLES = [
  { cmd: "/run pytest -q", out: "78 passed in 8.80s" },
  { cmd: "/pkg pip install httpx", out: "Successfully installed httpx" },
  { cmd: "/plan add jwt auth", out: "Plan · 4 steps ready" },
] as const;

const HERO_MODELS = [
  { id: "groq/llama-3.3-70b", meta: "128k ctx" },
  { id: "gemini/2.5-flash", meta: "1M ctx" },
  { id: "nvidia/nemotron-70b", meta: "128k ctx" },
] as const;

const MARQUEE_STACK = [
  { name: "Groq", role: "Fast inference" },
  { name: "Google Gemini", role: "Reasoning" },
  { name: "NVIDIA NIM", role: "Open weights" },
  { name: "Pinecone", role: "Vector RAG" },
  { name: "Firebase", role: "Auth & sync" },
  { name: "LangChain", role: "Tool runtime" },
  { name: "DuckDuckGo", role: "Web search" },
  { name: "Python", role: "CLI core" },
  { name: "Next.js", role: "Docs & web" },
] as const;

const CAPABILITIES = [
  {
    title: "Bring your own keys",
    desc: "Use your own Groq, Google Gemini, and NVIDIA NIM keys. Switch models anytime with /model without lock-in.",
  },
  {
    title: "Sandboxed /run & /pkg",
    desc: "Execute shell commands and install packages via pip, uv, npm, cargo, brew, or apt behind a denylist & approval gate.",
  },
  {
    title: "Pinecone Cloud RAG",
    desc: "Index your codebase with /index and retrieve exact semantic chunks with file citations via /search.",
  },
  {
    title: "AES-256-GCM key vault",
    desc: "Keys are encrypted client-side with Argon2id + AES-256-GCM before optional Firebase ciphertext sync.",
  },
  {
    title: "Durable JSON sessions",
    desc: "Every conversation persists locally as JSON. Open fresh context with /new, inspect /budget, or /compact older turns.",
  },
  {
    title: "Explicit approval gate",
    desc: "Every file write, edit, deletion, or shell command previews its diff and waits for [Y/n/a] unless /auto is on.",
  },
];

const COMING_SOON_ITEMS = [
  {
    id: "mcp",
    title: "MCP Bridges",
    subtitle: "Connect local & remote tool servers",
    preview: "$ valkyria mcp add postgres --scope workspace",
    detail:
      "Expose databases, issue trackers, and internal APIs to Valkyria through Model Context Protocol behind the same approval gate.",
    icon: "mcp" as const,
  },
  {
    id: "voice",
    title: "Voice Control",
    subtitle: "Talk to command your laptop",
    preview: "$ valkyria voice --wake hands-free",
    detail:
      "Speak natural instructions to navigate repos, execute tests, install dependencies, and confirm diffs aloud.",
    icon: "voice" as const,
  },
  {
    id: "mobile",
    title: "Mobile Remote",
    subtitle: "Steer & approve from your phone",
    preview: "$ valkyria pair --mobile",
    detail:
      "Inspect live agent runs, review pending file diffs, and approve or deny shell commands straight from your phone.",
    icon: "mobile" as const,
  },
];

const STACK_NODES = [
  { name: "Groq", role: "Ultra-fast inference", tag: "LLM Provider" },
  { name: "Google Gemini", role: "Reasoning & context", tag: "LLM Provider" },
  { name: "NVIDIA NIM", role: "Open-weights catalog", tag: "LLM Provider" },
  { name: "Pinecone", role: "Vector index & citations", tag: "Cloud RAG" },
  { name: "Firebase Auth", role: "Sign-in & vault sync", tag: "Identity" },
  { name: "LangChain", role: "Unified tool calling", tag: "Agent Core" },
  { name: "DuckDuckGo", role: "Live web search (/web)", tag: "Retrieval" },
  { name: "Python", role: "Click, Rich, Argon2id", tag: "CLI Runtime" },
  { name: "Next.js", role: "Docs & callback UI", tag: "Web Surface" },
];

const GITHUB_URL = "https://github.com/Anupam2005-tech/valkyria-cli";

export function HomeClient() {
  const [activeId, setActiveId] = useState<string>("overview");
  const [activeStep, setActiveStep] = useState<number>(0);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [cmdIndex, setCmdIndex] = useState(0);
  const [selectedModel, setSelectedModel] = useState(0);
  const [gateApproved, setGateApproved] = useState<boolean | null>(null);
  const [activeHorizon, setActiveHorizon] = useState<number>(0);

  useEffect(() => {
    const elements = RAIL_SECTIONS.map((s) => document.getElementById(s.id)).filter(
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
      { rootMargin: "-18% 0px -62% 0px", threshold: 0 }
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const copyCommand = (key: string, value: string) => {
    navigator.clipboard?.writeText(value);
    setCopiedKey(key);
    setTimeout(() => {
      setCopiedKey((prev) => (prev === key ? null : prev));
    }, 1800);
  };

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="min-h-screen bg-[#101113] text-[#F2F4F1] selection:bg-[#FFC929] selection:text-[#101113]">
      {/* Subtle architectural dot-grid backdrop */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.26]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(242, 244, 241, 0.14) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Minimal sticky utility header */}
      <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#101113]/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1380px] items-center justify-between px-5 sm:px-8">
          <Link
            href="/"
            className="flex items-center gap-2.5 text-[#F2F4F1] transition-opacity hover:opacity-90"
          >
            <Logo size={24} />
            <span className="font-[family-name:var(--font-mono)] text-sm font-semibold tracking-tight">
              valkyria
            </span>
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/docs"
              className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
            >
              Docs
            </Link>
            <button
              type="button"
              onClick={() => scrollToSection("changelog")}
              className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
            >
              Changelog
            </button>
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
              onClick={() => scrollToSection("get-started")}
              className="inline-flex items-center gap-1.5 rounded border border-white/20 px-3 py-1 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
            >
              Install
            </button>
          </nav>

          <button
            type="button"
            onClick={() => setMobileMenuOpen((v) => !v)}
            aria-label="Toggle navigation"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/10 text-[#F2F4F1] md:hidden"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>

        {/* Mobile menu drawer */}
        {mobileMenuOpen && (
          <div className="border-t border-white/[0.07] bg-[#101113] px-5 py-4 md:hidden">
            <div className="flex flex-col gap-3">
              {RAIL_SECTIONS.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => scrollToSection(s.id)}
                  className={`flex items-center gap-3 text-left font-[family-name:var(--font-mono)] text-xs ${
                    activeId === s.id ? "text-[#FFC929]" : "text-[#9499A0]"
                  }`}
                >
                  <span className="opacity-60">[{s.num}]</span>
                  <span>{s.label}</span>
                </button>
              ))}
              <div className="mt-2 flex items-center gap-4 border-t border-white/[0.07] pt-3">
                <Link
                  href="/docs"
                  className="font-[family-name:var(--font-mono)] text-xs text-[#F2F4F1]"
                >
                  Docs
                </Link>
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0]"
                >
                  GitHub
                </a>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main layout: Sticky Left Index Rail + Wide Editorial Content Column */}
      <div className="relative z-10 mx-auto max-w-[1380px] px-5 sm:px-8">
        <div className="lg:grid lg:grid-cols-[200px_minmax(0,1fr)] lg:gap-12">
          {/* Left sticky navigation rail */}
          <aside className="hidden lg:block lg:self-start lg:sticky lg:top-20">
            <div className="py-6">
              <nav aria-label="Section index" className="flex flex-col gap-2.5">
                {RAIL_SECTIONS.map((s) => {
                  const isActive = activeId === s.id;
                  return (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => scrollToSection(s.id)}
                      className={`group flex items-center gap-2.5 text-left font-[family-name:var(--font-mono)] text-xs transition-colors ${
                        isActive
                          ? "text-[#FFC929]"
                          : "text-[#6F747A] hover:text-[#F2F4F1]"
                      }`}
                    >
                      <span
                        className={`tabular-nums transition-opacity ${
                          isActive ? "opacity-100" : "opacity-60 group-hover:opacity-100"
                        }`}
                      >
                        [{s.num}]
                      </span>
                      <span>{s.label}</span>
                    </button>
                  );
                })}
              </nav>

              <div className="mt-8 border-t border-white/[0.07] pt-5">
                <Link
                  href="/docs"
                  className="inline-flex items-center gap-1.5 font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#FFC929]"
                >
                  Manual &amp; commands
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </aside>

          {/* Right editorial content column */}
          <main className="min-w-0">
            {/* ── [1] OVERVIEW / HERO ─────────────────────────────────────── */}
            <section id="overview" className="pb-14 pt-10 sm:pt-14">
              <h1 className="max-w-3xl text-[clamp(36px,5.2vw,60px)] font-semibold leading-[1.04] tracking-[-0.03em] text-[#F2F4F1]">
                Own your keys.{" "}
                <span className="block sm:inline">
                  Command your{" "}
                  <span className="font-[family-name:var(--font-accent)] font-normal italic text-[#FFC929]">
                    terminal.
                  </span>
                </span>
              </h1>

              <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#9499A0] sm:text-[17px]">
               Plan, search, and ship from your terminal. Multi-model routing, semantic codebase memory, encrypted BYOK, and approval-gated edits.
              </p>

              {/* 4-column enlarged borderless showcase grid with transparent buttons */}
              <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
                {/* Item 1: Terminal */}
                <div className="group flex flex-col justify-between">
                  <div>
                    <button
                      type="button"
                      onClick={() =>
                        setCmdIndex((i) => (i + 1) % HERO_CMD_SAMPLES.length)
                      }
                      title="Click to cycle command"
                      className="relative flex h-72 w-full flex-col justify-between overflow-hidden border border-white/[0.08] bg-[#16171B] p-5 text-left font-[family-name:var(--font-mono)] text-xs transition-colors group-hover:border-white/[0.18]"
                    >
                      <div className="select-none text-center text-2xl font-bold tracking-[0.22em] text-white/[0.08]">
                        VALKYRIA
                      </div>

                      <div className="rounded border border-white/[0.08] bg-[#0E0F12] p-3.5 shadow-2xl">
                        <div className="flex items-center justify-between text-[10px] text-[#6F747A]">
                          <span>repl · v0.1.3</span>
                          <span className="inline-flex items-center gap-1 text-[#FFC929]">
                            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#FFC929]" />
                            ready
                          </span>
                        </div>
                        <div className="mt-3 space-y-1.5 text-[11px] text-[#E5E7EB]">
                          <div className="text-[#6F747A]">$ valkyria</div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[#FFC929]">›</span>
                            <span>{HERO_CMD_SAMPLES[cmdIndex].cmd}</span>
                            <span className="inline-block h-3.5 w-1.5 animate-pulse bg-[#FFC929]" />
                          </div>
                          <div className="text-emerald-400">
                            {HERO_CMD_SAMPLES[cmdIndex].out}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-[#6F747A]">
                        <span>click preview to cycle</span>
                        <span>esc interrupt</span>
                      </div>
                    </button>

                    <h2 className="mt-4 text-[15px] font-semibold text-[#F2F4F1]">
                      Terminal
                    </h2>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#9499A0]">
                      Fast Python REPL with `/` slash completion, `@` file context,
                      and sandboxed `/run` &amp; `/pkg`.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => copyCommand("hero-install", "pipx install valkyria-cli")}
                    className="mt-4 inline-flex w-fit items-center gap-2.5 border border-white/20 bg-transparent px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                  >
                    <span>
                      {copiedKey === "hero-install" ? "Copied command" : "Install CLI"}
                    </span>
                    {copiedKey === "hero-install" ? (
                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="h-3.5 w-3.5 opacity-70" />
                    )}
                  </button>
                </div>

                {/* Item 2: Multi-Model */}
                <div className="group flex flex-col justify-between">
                  <div>
                    <div className="flex h-72 w-full flex-col justify-between border border-white/[0.08] bg-[#16171B] p-5 font-[family-name:var(--font-mono)] text-xs transition-colors group-hover:border-white/[0.18]">
                      <div className="flex items-center justify-between text-[10px] text-[#6F747A]">
                        <span>/model pick</span>
                        <span>BYOK</span>
                      </div>

                      <div className="space-y-2">
                        {HERO_MODELS.map((m, idx) => {
                          const active = selectedModel === idx;
                          return (
                            <button
                              key={m.id}
                              type="button"
                              onClick={() => setSelectedModel(idx)}
                              className={`flex w-full items-center justify-between border px-3 py-2 text-left text-[11px] transition ${
                                active
                                  ? "border-[#FFC929]/50 bg-[#FFC929]/10 text-[#F2F4F1]"
                                  : "border-white/[0.06] bg-[#0E0F12]/80 text-[#9499A0] hover:border-white/20 hover:text-[#F2F4F1]"
                              }`}
                            >
                              <span className="truncate">{m.id}</span>
                              <span
                                className={
                                  active ? "text-[#FFC929]" : "text-[#6F747A]"
                                }
                              >
                                {active ? "active" : m.meta}
                              </span>
                            </button>
                          );
                        })}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-[#6F747A]">
                        <span>click model to switch</span>
                        <span>3 providers</span>
                      </div>
                    </div>

                    <h2 className="mt-4 text-[15px] font-semibold text-[#F2F4F1]">
                      Multi-Model
                    </h2>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#9499A0]">
                      Route tasks across Groq, Gemini, and NVIDIA on your own keys.
                      Inspect budgets before switching.
                    </p>
                  </div>

                  <Link
                    href="/docs"
                    className="mt-4 inline-flex w-fit items-center gap-2.5 border border-white/20 bg-transparent px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                  >
                    <span>Read docs</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>

                {/* Item 3: Approval Gate (Halftone Shield Orb visual) */}
                <div className="group flex flex-col justify-between">
                  <div>
                    <div className="flex h-72 w-full flex-col items-center justify-between border border-white/[0.08] bg-[#16171B] p-5 font-[family-name:var(--font-mono)] text-xs transition-colors group-hover:border-white/[0.18]">
                      <div className="flex w-full items-center justify-between text-[10px] text-[#6F747A]">
                        <span className="inline-flex items-center gap-1.5 text-[#FFC929]">
                          <Shield className="h-3 w-3" />
                          GATE
                        </span>
                        <span>denylist active</span>
                      </div>

                      {/* Halftone dotted shield emblem */}
                      <div className="relative flex h-32 w-32 items-center justify-center">
                        <div
                          className="h-28 w-28 rounded-full border border-white/10"
                          style={{
                            backgroundImage:
                              "radial-gradient(rgba(242,244,241,0.45) 1.2px, transparent 1.2px)",
                            backgroundSize: "6px 6px",
                            maskImage:
                              "radial-gradient(circle, black 48%, transparent 72%)",
                            WebkitMaskImage:
                              "radial-gradient(circle, black 48%, transparent 72%)",
                          }}
                        />
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                          <span className="text-[10px] text-[#FFC929]">
                            pip install httpx
                          </span>
                          <span className="mt-1 text-[10px] text-[#A3A7AB]">
                            {gateApproved === null
                              ? "awaiting [Y/n]"
                              : gateApproved
                              ? "APPROVED"
                              : "BLOCKED"}
                          </span>
                        </div>
                      </div>

                      <div className="flex w-full items-center justify-center gap-2">
                        <button
                          type="button"
                          onClick={() => setGateApproved(true)}
                          className={`border px-2.5 py-1 text-[10px] transition ${
                            gateApproved === true
                              ? "border-emerald-400/60 text-emerald-300"
                              : "border-white/15 text-[#9499A0] hover:border-white/30 hover:text-[#F2F4F1]"
                          }`}
                        >
                          [y] Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => setGateApproved(false)}
                          className={`border px-2.5 py-1 text-[10px] transition ${
                            gateApproved === false
                              ? "border-red-400/60 text-red-300"
                              : "border-white/15 text-[#9499A0] hover:border-white/30 hover:text-[#F2F4F1]"
                          }`}
                        >
                          [n] Deny
                        </button>
                      </div>
                    </div>

                    <h2 className="mt-4 text-[15px] font-semibold text-[#F2F4F1]">
                      Safety Gate
                    </h2>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#9499A0]">
                      Every file edit, shell command, and package install shows a
                      diff and waits for your explicit yes.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => scrollToSection("flight-path")}
                    className="mt-4 inline-flex w-fit items-center gap-2.5 border border-white/20 bg-transparent px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                  >
                    <span>See workflow</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Item 4: Vault & RAG (Code syntax style like SDK card) */}
                <div className="group flex flex-col justify-between">
                  <div>
                    <div className="flex h-72 w-full flex-col justify-between border border-white/[0.08] bg-[#16171B] p-5 font-[family-name:var(--font-mono)] text-[11px] transition-colors group-hover:border-white/[0.18]">
                      <div className="flex items-center justify-between text-[10px] text-[#6F747A]">
                        <span>vault · rag</span>
                        <span className="text-emerald-400">AES-256-GCM</span>
                      </div>

                      <pre className="overflow-x-hidden leading-6 text-[#D6D9DF]">
                        <span className="text-[#FFC929]">from</span> valkyria{" "}
                        <span className="text-[#FFC929]">import</span> vault{"\n"}
                        {"\n"}
                        keys = vault.unlock(pw){"\n"}
                        hits = rag.query(
                        <span className="text-emerald-300">&quot;auth&quot;</span>)
                        {"\n"}
                        <span className="text-[#6F747A]"># 3 citations · local</span>
                      </pre>

                      <div className="flex items-center justify-between text-[10px] text-[#6F747A]">
                        <span>ciphertext-only sync</span>
                        <span>Pinecone</span>
                      </div>
                    </div>

                    <h2 className="mt-4 text-[15px] font-semibold text-[#F2F4F1]">
                      Vault &amp; RAG
                    </h2>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#9499A0]">
                      Client-side Argon2id + AES-256-GCM key encryption paired with
                      Pinecone semantic code retrieval.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => copyCommand("hero-login", "valkyria login")}
                    className="mt-4 inline-flex w-fit items-center gap-2.5 border border-white/20 bg-transparent px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                  >
                    <span>
                      {copiedKey === "hero-login" ? "Copied command" : "$ valkyria login"}
                    </span>
                    {copiedKey === "hero-login" ? (
                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="h-3.5 w-3.5 opacity-70" />
                    )}
                  </button>
                </div>
              </div>

              {/* Moving stack marquee with logos */}
              <div className="mt-12 border-y border-white/[0.07] py-4">
                <div className="flex items-center gap-6">
                  <span className="hidden shrink-0 font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-wider text-[#6F747A] sm:block">
                    Built with
                  </span>
                  <div className="vk-marquee min-w-0 flex-1 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
                    <div className="vk-marquee-track items-center gap-8">
                      {[...MARQUEE_STACK, ...MARQUEE_STACK].map((item, idx) => (
                        <div
                          key={`${item.name}-${idx}`}
                          className="flex shrink-0 items-center gap-2.5 text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
                        >
                          <BrandLogo name={item.name} className="h-4 w-4 shrink-0" />
                          <span className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#D6D9DF]">
                            {item.name}
                          </span>
                          <span className="font-[family-name:var(--font-mono)] text-[10px] text-[#6F747A]">
                            · {item.role}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* ── [2] WHAT IS VALKYRIA? ─────────────────────────────────── */}
            <section
              id="capabilities"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    What is Valkyria?
                  </h2>
                </div>

                <div>
                  <p className="max-w-2xl text-base leading-relaxed text-[#A3A7AB] sm:text-lg">
                    Valkyria is a terminal-first AI workspace built for developers
                    who refuse black-box tooling. Connect your own API keys, inspect
                    every action before it runs, and keep your credentials encrypted
                    on your own machine.{" "}
                    <Link
                      href="/docs"
                      className="text-[#F2F4F1] underline decoration-[#FFC929]/60 underline-offset-4 transition hover:text-[#FFC929]"
                    >
                      Read the manual.
                    </Link>
                  </p>

                  <div className="mt-10 grid grid-cols-1 gap-x-10 gap-y-8 sm:grid-cols-2">
                    {CAPABILITIES.map((item) => (
                      <div key={item.title}>
                        <h3 className="text-sm font-semibold text-[#F2F4F1]">
                          {item.title}
                        </h3>
                        <p className="mt-1.5 text-sm leading-relaxed text-[#9499A0]">
                          {item.desc}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* ── [3] FLIGHT PATH (HOW IT WORKS) ────────────────────────── */}
            <section
              id="flight-path"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Flight path
                  </h2>
                  <p className="mt-2 text-xs leading-relaxed text-[#6F747A]">
                    Four moves from prompt to verified output.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.1fr]">
                  {/* Step selector */}
                  <div className="flex flex-col divide-y divide-white/[0.07] border-y border-white/[0.07]">
                    {HOW_IT_WORKS_STEPS.map((step, idx) => {
                      const active = activeStep === idx;
                      return (
                        <button
                          key={step.num}
                          type="button"
                          onClick={() => setActiveStep(idx)}
                          className={`flex items-start gap-4 py-4 text-left transition-colors ${
                            active ? "text-[#F2F4F1]" : "text-[#6F747A] hover:text-[#A3A7AB]"
                          }`}
                        >
                          <span
                            className={`font-[family-name:var(--font-mono)] text-xs tabular-nums ${
                              active ? "text-[#FFC929]" : "text-[#6F747A]"
                            }`}
                          >
                            {step.num}
                          </span>
                          <div>
                            <div className="text-sm font-semibold">{step.title}</div>
                            {active && (
                              <p className="mt-1.5 text-xs leading-relaxed text-[#9499A0]">
                                {step.copy}
                              </p>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Active terminal preview */}
                  <div className="flex flex-col justify-between rounded-lg border border-white/[0.09] bg-[#0D0E10] p-5 font-[family-name:var(--font-mono)] text-xs">
                    <div className="flex items-center justify-between border-b border-white/[0.07] pb-3 text-[11px] text-[#6F747A]">
                      <span className="inline-flex items-center gap-2">
                        <Terminal className="h-3.5 w-3.5 text-[#FFC929]" />
                        {HOW_IT_WORKS_STEPS[activeStep].command}
                      </span>
                      <span>step {HOW_IT_WORKS_STEPS[activeStep].num}</span>
                    </div>

                    <pre className="my-5 overflow-x-auto leading-6 text-[#D6D9DF]">
                      {HOW_IT_WORKS_STEPS[activeStep].snippet.join("\n")}
                    </pre>

                    <div className="flex items-center justify-between border-t border-white/[0.07] pt-3 text-[11px] text-[#6F747A]">
                      <span>approval gate enabled</span>
                      <span className="text-[#FFC929]">valkyria repl</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* ── [4] GET STARTED ───────────────────────────────────────── */}
            <section
              id="get-started"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Get started
                  </h2>
                </div>

                <div>
                  <p className="max-w-xl text-sm leading-relaxed text-[#A3A7AB] sm:text-base">
                    Install the Python CLI, sign in through your browser, and add
                    your own provider keys. Nothing runs without your say-so.
                  </p>

                  <div className="mt-8 divide-y divide-white/[0.08] border-y border-white/[0.08]">
                    {[
                      {
                        num: "01",
                        title: "Install",
                        desc: "Requires Python 3.12+. Install globally with pipx or uv.",
                        cmd: "pipx install valkyria-cli",
                      },
                      {
                        num: "02",
                        title: "Log in & unlock vault",
                        desc: "Authenticates via browser callback and encrypts keys locally with AES-256-GCM.",
                        cmd: "valkyria login",
                      },
                      {
                        num: "03",
                        title: "Launch in your project",
                        desc: "Index files with /index, switch models with /model, or run commands with /run & /pkg.",
                        cmd: "valkyria",
                      },
                    ].map((row) => (
                      <div
                        key={row.num}
                        className="flex flex-col justify-between gap-4 py-5 sm:flex-row sm:items-center"
                      >
                        <div className="flex items-start gap-6">
                          <span className="font-[family-name:var(--font-mono)] text-xs text-[#FFC929] tabular-nums">
                            {row.num}
                          </span>
                          <div>
                            <h3 className="text-sm font-semibold text-[#F2F4F1]">
                              {row.title}
                            </h3>
                            <p className="mt-1 text-xs text-[#9499A0]">{row.desc}</p>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => copyCommand(`step-${row.num}`, row.cmd)}
                          className="inline-flex shrink-0 items-center justify-between gap-3 border border-white/20 bg-transparent px-3.5 py-2 font-[family-name:var(--font-mono)] text-xs text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                        >
                          <span>$ {row.cmd}</span>
                          {copiedKey === `step-${row.num}` ? (
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="h-3.5 w-3.5 text-[#6F747A]" />
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* ── [5] COMING SOON: COMPACT STRIP (MCP + VOICE + MOBILE) ── */}
            <section
              id="coming-soon"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Coming soon
                  </h2>
                  <p className="mt-2 text-xs leading-relaxed text-[#6F747A]">
                    Expanding the flight deck.
                  </p>
                </div>

                <div>
                  {/* Compact 3-cell horizontal strip modeled cleanly */}
                  <div className="grid grid-cols-1 divide-y divide-white/[0.08] border border-white/[0.09] bg-[#141518] md:grid-cols-3 md:divide-x md:divide-y-0">
                    {COMING_SOON_ITEMS.map((item, idx) => {
                      const active = activeHorizon === idx;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => setActiveHorizon(idx)}
                          className={`flex items-center gap-3.5 p-4 text-left transition-colors ${
                            active ? "bg-[#1A1C21]" : "hover:bg-[#17191D]"
                          }`}
                        >
                          <div
                            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-md border ${
                              active
                                ? "border-[#FFC929]/50 bg-[#FFC929]/10 text-[#FFC929]"
                                : "border-white/10 bg-[#0D0E10] text-[#D6D9DF]"
                            }`}
                          >
                            {item.icon === "mcp" && <Plug className="h-4 w-4" />}
                            {item.icon === "voice" && <Mic className="h-4 w-4" />}
                            {item.icon === "mobile" && <Smartphone className="h-4 w-4" />}
                          </div>

                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="truncate text-sm font-semibold text-[#F2F4F1]">
                                {item.title}
                              </span>
                              <span className="shrink-0 font-[family-name:var(--font-mono)] text-[9px] uppercase tracking-wider text-[#FFC929]">
                                Soon
                              </span>
                            </div>
                            <p className="mt-0.5 truncate text-xs text-[#9499A0]">
                              {item.subtitle}
                            </p>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Single-row interactive detail bar for selected Coming Soon item */}
                  <div className="flex flex-col justify-between gap-2 border-x border-b border-white/[0.09] bg-[#0E0F12] px-4 py-3 text-xs sm:flex-row sm:items-center">
                    <span className="text-[#9499A0]">
                      {COMING_SOON_ITEMS[activeHorizon].detail}
                    </span>
                    <code className="shrink-0 font-[family-name:var(--font-mono)] text-[11px] text-[#FFC929]">
                      {COMING_SOON_ITEMS[activeHorizon].preview}
                    </code>
                  </div>
                </div>
              </div>
            </section>

            {/* ── [6] STACK & COMPARISON ────────────────────────────────── */}
            <section
              id="stack"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Bring your own keys
                  </h2>
                </div>

                <div>
                  <p className="max-w-xl text-sm leading-relaxed text-[#A3A7AB] sm:text-base">
                    Built on proven providers and open tools. Bring your own keys
                    and pay providers directly—zero markup, zero key custody.
                  </p>

                  {/* Crisp bordered 1px hairline grid WITH logos */}
                  <div className="mt-8 grid grid-cols-2 border-l border-t border-white/[0.09] sm:grid-cols-3">
                    {STACK_NODES.map((node) => (
                      <div
                        key={node.name}
                        className="group flex flex-col justify-between border-b border-r border-white/[0.09] bg-[#121316] p-5 transition-colors hover:bg-[#17191D]"
                      >
                        <div className="flex items-center justify-between">
                          <BrandLogo
                            name={node.name}
                            className="h-5 w-5 text-[#A3A7AB] transition-colors group-hover:text-[#F2F4F1]"
                          />
                          <span className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-wider text-[#6F747A]">
                            {node.tag}
                          </span>
                        </div>
                        <div className="mt-5">
                          <div className="text-sm font-semibold text-[#F2F4F1]">
                            {node.name}
                          </div>
                          <div className="mt-0.5 text-xs text-[#9499A0]">
                            {node.role}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Comparison table */}
                  <div className="mt-12 overflow-hidden border border-white/[0.09] bg-[#151619]">
                    <div className="grid grid-cols-1 border-b border-white/[0.08] bg-[#101113] px-5 py-3 font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-wider text-[#6F747A] sm:grid-cols-[140px_1fr_1fr] sm:gap-6">
                      <span>Dimension</span>
                      <span className="hidden sm:block">Typical AI CLI</span>
                      <span className="hidden text-[#FFC929] sm:block">Valkyria</span>
                    </div>
                    <div className="divide-y divide-white/[0.07]">
                      {COMPARISON_ROWS.map((row) => (
                        <div
                          key={row.feature}
                          className="grid grid-cols-1 gap-2 px-5 py-4 text-xs sm:grid-cols-[140px_1fr_1fr] sm:items-center sm:gap-6"
                        >
                          <div className="font-[family-name:var(--font-mono)] font-medium text-[#F2F4F1]">
                            {row.feature}
                          </div>
                          <div className="text-[#6F747A]">{row.typical}</div>
                          <div className="text-[#D6D9DF]">{row.valkyria}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* ── [7] CHANGELOG: ACETERNITY TIMELINE FOR VALKYRIA ───────── */}
            <section
              id="changelog"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div className="md:sticky md:top-24 md:self-start">
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Changelog
                  </h2>
                  <p className="mt-2 text-xs leading-relaxed text-[#6F747A]">
                    Scroll to trace every shipped release.
                  </p>
                </div>

                <div className="relative w-full overflow-clip">
                  <Timeline data={VALKYRIA_TIMELINE_DATA} hideHeader />
                </div>
              </div>
            </section>

            {/* ── [8] QUESTIONS ─────────────────────────────────────────── */}
            <section
              id="faq"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Questions
                  </h2>
                </div>

                <div className="divide-y divide-white/[0.08] border-y border-white/[0.08]">
                  {FAQ_ITEMS.map((item, idx) => {
                    const isOpen = openFaq === idx;
                    return (
                      <div key={item.q}>
                        <button
                          type="button"
                          aria-expanded={isOpen}
                          onClick={() => setOpenFaq(isOpen ? null : idx)}
                          className="flex w-full items-center justify-between gap-4 py-4 text-left text-sm font-medium text-[#F2F4F1] transition hover:text-[#FFC929]"
                        >
                          <span>{item.q}</span>
                          <ChevronDown
                            className={`h-4 w-4 shrink-0 text-[#6F747A] transition-transform duration-200 ${
                              isOpen ? "rotate-180 text-[#FFC929]" : ""
                            }`}
                          />
                        </button>
                        {isOpen && (
                          <p className="pb-4 pr-8 text-xs leading-relaxed text-[#9499A0] sm:text-sm">
                            {item.a}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* ── [9] OPEN SOURCE ───────────────────────────────────────── */}
            <section
              id="open-source"
              className="border-t border-white/[0.08] py-16 sm:py-20"
            >
              <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_minmax(0,1fr)] md:gap-12">
                <div>
                  <h2 className="font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1]">
                    Open source
                  </h2>
                </div>

                <div>
                  <p className="max-w-xl text-sm leading-relaxed text-[#A3A7AB] sm:text-base">
                    Valkyria CLI is MIT-licensed and built in the open. Inspect the
                    security gate, audit the AES-256-GCM vault, or extend the tool
                    registry yourself.
                  </p>

                  <div className="mt-6 flex flex-wrap items-center gap-3">
                    <a
                      href={GITHUB_URL}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 border border-white/20 bg-transparent px-4 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                    >
                      <Github className="h-3.5 w-3.5" />
                      View on GitHub
                    </a>
                    <Link
                      href="/docs"
                      className="inline-flex items-center gap-2 border border-white/20 bg-transparent px-4 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
                    >
                      Command reference
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            </section>
          </main>
        </div>
      </div>

      <FooterSection />
    </div>
  );
}

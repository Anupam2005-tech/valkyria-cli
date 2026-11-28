"use client";

import React from "react";
import { Timeline, type TimelineEntry } from "@/components/ui/timeline";

export const VALKYRIA_TIMELINE_DATA: TimelineEntry[] = [
  {
    title: "v0.1.3",
    content: (
      <div className="border border-white/[0.08] bg-[#141518] p-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="bg-[#FFC929]/15 px-2 py-0.5 font-[family-name:var(--font-mono)] text-[10px] font-medium text-[#FFC929] ring-1 ring-[#FFC929]/30">
            LATEST
          </span>
          <span className="font-[family-name:var(--font-mono)] text-xs text-[#6F747A]">
            Nov 28, 2026
          </span>
        </div>
        <h4 className="mt-2.5 text-sm font-semibold text-[#F2F4F1]">
          Sandboxed /run, /pkg &amp; Valkyria rebrand
        </h4>
        <ul className="mt-3 space-y-2 text-xs leading-relaxed text-[#A3A7AB]">
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]" />
            <span>
              Added <code className="text-[#F2F4F1]">run_command</code> (<code className="text-[#FFC929]">/run</code>) with workspace cwd lock, 60s timeout, and destructive command denylist.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]" />
            <span>
              Added <code className="text-[#F2F4F1]">pkg_install</code> (<code className="text-[#FFC929]">/pkg</code>) supporting pip, pip3, uv, pipx, npm, yarn, pnpm, cargo, brew, apt, and dnf.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]" />
            <span>
              Propagated <code className="text-[#F2F4F1]">/auto</code> runtime approvals and moved Firebase API configuration into <code className="text-[#F2F4F1]">.env</code>.
            </span>
          </li>
        </ul>
      </div>
    ),
  },
  {
    title: "v0.1.2",
    content: (
      <div className="border border-white/[0.08] bg-[#141518] p-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="bg-white/[0.05] px-2 py-0.5 font-[family-name:var(--font-mono)] text-[10px] font-medium text-[#9499A0]">
            RELEASE
          </span>
          <span className="font-[family-name:var(--font-mono)] text-xs text-[#6F747A]">
            Nov 26, 2026
          </span>
        </div>
        <h4 className="mt-2.5 text-sm font-semibold text-[#F2F4F1]">
          CLI packaging &amp; workspace stability
        </h4>
        <ul className="mt-3 space-y-2 text-xs leading-relaxed text-[#A3A7AB]">
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]/70" />
            <span>
              Published <code className="text-[#F2F4F1]">valkyria-cli</code> wheel &amp; entrypoints (<code className="text-[#F2F4F1]">valkyria</code>, <code className="text-[#F2F4F1]">vk</code>) with cleaner session metadata cards.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]/70" />
            <span>
              Protected CLI-only browser login callback flow and refined <code className="text-[#F2F4F1]">/account</code> lifecycle commands.
            </span>
          </li>
        </ul>
      </div>
    ),
  },
  {
    title: "v0.1.1",
    content: (
      <div className="border border-white/[0.08] bg-[#141518] p-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="bg-white/[0.05] px-2 py-0.5 font-[family-name:var(--font-mono)] text-[10px] font-medium text-[#9499A0]">
            UPDATE
          </span>
          <span className="font-[family-name:var(--font-mono)] text-xs text-[#6F747A]">
            Nov 25, 2026
          </span>
        </div>
        <h4 className="mt-2.5 text-sm font-semibold text-[#F2F4F1]">
          Interactive REPL &amp; @path context
        </h4>
        <ul className="mt-3 space-y-2 text-xs leading-relaxed text-[#A3A7AB]">
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]/70" />
            <span>
              Added <code className="text-[#F2F4F1]">@workspace</code> path autocomplete, slash command prefix filtering, and Rich tool action cards.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]/70" />
            <span>
              Added <code className="text-[#F2F4F1]">/budget</code>, <code className="text-[#F2F4F1]">/compact</code>, and <code className="text-[#F2F4F1]">/new</code> session controls with live token estimation.
            </span>
          </li>
        </ul>
      </div>
    ),
  },
  {
    title: "v0.1.0",
    content: (
      <div className="border border-white/[0.08] bg-[#141518] p-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="bg-white/[0.05] px-2 py-0.5 font-[family-name:var(--font-mono)] text-[10px] font-medium text-[#9499A0]">
            INITIAL
          </span>
          <span className="font-[family-name:var(--font-mono)] text-xs text-[#6F747A]">
            Nov 24, 2026
          </span>
        </div>
        <h4 className="mt-2.5 text-sm font-semibold text-[#F2F4F1]">
          Multi-model agent, vault &amp; Pinecone RAG
        </h4>
        <ul className="mt-3 space-y-2 text-xs leading-relaxed text-[#A3A7AB]">
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]/70" />
            <span>
              Launched streaming chat across Groq, Google Gemini, and NVIDIA NIM on user-owned API keys.
            </span>
          </li>
          <li className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#FFC929]/70" />
            <span>
              Shipped Argon2id + AES-256-GCM local key vault, encrypted Firebase sync, and Pinecone code indexing.
            </span>
          </li>
        </ul>
      </div>
    ),
  },
];

export default function TimelineDemo() {
  return (
    <div className="relative w-full overflow-clip">
      <Timeline data={VALKYRIA_TIMELINE_DATA} />
    </div>
  );
}


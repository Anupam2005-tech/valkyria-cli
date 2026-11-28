"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Terminal } from "lucide-react";

interface PackageManagerOption {
  id: "pipx" | "uv" | "pip";
  label: string;
  command: string;
  note: string;
}

const PACKAGE_MANAGERS: PackageManagerOption[] = [
  {
    id: "pipx",
    label: "pipx",
    command: "pipx install valkyria-cli",
    note: "Recommended · Isolated Python CLI environment",
  },
  {
    id: "uv",
    label: "uv",
    command: "uv tool install valkyria-cli",
    note: "Fastest · Installs valkyrie and vk binaries globally",
  },
  {
    id: "pip",
    label: "pip",
    command: "pip install valkyria-cli",
    note: "Standard · Installs inside your active Python 3.12+ venv",
  },
];

const QUICKSTART_STEPS = [
  { cmd: "valkyrie login", out: "Authenticate with Firebase in your browser" },
  { cmd: "valkyrie init", out: "Encrypt Groq, Gemini, and NVIDIA keys (AES-256-GCM)" },
  { cmd: "/index .", out: "Chunk and upsert workspace vectors to Pinecone" },
  { cmd: "/plan <task>", out: "Generate a step-by-step flight plan before touching disk" },
  { cmd: "/build", out: "Execute with diff previews and explicit approval gates" },
];

export default function Download8() {
  const [selectedPm, setSelectedPm] = useState<PackageManagerOption>(
    PACKAGE_MANAGERS[0]
  );

  return (
    <div className="mx-auto max-w-[980px] rounded-[20px] border border-[rgba(242,244,241,0.12)] bg-[#151619] overflow-hidden">
      {/* Top window bar + package manager tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[rgba(242,244,241,0.08)] bg-[#101113] px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <Terminal className="h-4 w-4 text-[#FFC929]" strokeWidth={1.5} />
          <span className="font-mono text-xs text-[#A3A7AB]">
            valkyrie-installer · Python 3.12+
          </span>
        </div>

        <div
          role="tablist"
          aria-label="Package manager"
          className="inline-flex items-center gap-1 rounded-[8px] border border-[rgba(242,244,241,0.10)] bg-[#151619] p-1"
        >
          {PACKAGE_MANAGERS.map((pm) => {
            const active = pm.id === selectedPm.id;
            return (
              <button
                key={pm.id}
                role="tab"
                type="button"
                aria-selected={active}
                onClick={() => setSelectedPm(pm)}
                className={`rounded-[6px] px-3 py-1 font-mono text-xs transition-colors ${
                  active
                    ? "bg-[#FFC929] text-[#1C1D20] font-medium"
                    : "text-[#A3A7AB] hover:text-[#F2F4F1]"
                }`}
              >
                {pm.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main terminal command bar */}
      <div className="p-5 sm:p-6">
        <div className="flex items-center justify-between rounded-[12px] border border-[rgba(242,244,241,0.14)] bg-[#101113] px-4 py-3">
          <div className="flex items-center gap-3 overflow-x-auto font-mono text-sm sm:text-base text-[#F2F4F1]">
            <span className="select-none text-[#FFC929]">$</span>
            <code className="whitespace-nowrap">{selectedPm.command}</code>
          </div>
          <span className="hidden sm:inline font-mono text-[11px] text-[#9499A0]">
            {selectedPm.label}
          </span>
        </div>

        <p className="mt-2.5 font-mono text-xs text-[#9499A0]">
          {selectedPm.note}
        </p>

        {/* Flight sequence inside terminal */}
        <div className="mt-5 divide-y divide-[rgba(242,244,241,0.08)] rounded-[12px] border border-[rgba(242,244,241,0.08)] bg-[#101113]/65">
          {QUICKSTART_STEPS.map((step, idx) => (
            <div
              key={step.cmd}
              className="flex flex-col gap-1.5 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-3 font-mono text-xs sm:text-sm">
                <span className="text-[#9499A0] tabular-nums">
                  0{idx + 1}
                </span>
                <span className="text-[#FFC929]">{step.cmd}</span>
              </div>
              <span className="text-xs sm:text-sm text-[#A3A7AB]">
                {step.out}
              </span>
            </div>
          ))}
        </div>

        {/* Bottom meta + manual link */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 pt-2">
          <div className="flex flex-wrap items-center gap-3 font-mono text-xs text-[#9499A0]">
            <span>Linux</span>
            <span>·</span>
            <span>macOS</span>
            <span>·</span>
            <span>Windows</span>
            <span>·</span>
            <span className="text-[#A3A7AB]">Short binary: vk</span>
          </div>

          <Link
            href="/docs"
            className="inline-flex items-center gap-1.5 font-mono text-xs text-[#F2F4F1] hover:text-[#FFC929] transition-colors"
          >
            <span>Read full manual</span>
            <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={1.5} />
          </Link>
        </div>
      </div>
    </div>
  );
}


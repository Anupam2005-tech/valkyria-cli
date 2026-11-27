"use client";

import React, { useEffect, useState } from "react";
import { scrollStore } from "@/lib/scroll-store";

interface ScriptFrame {
  lines: string[];
  showAutocomplete?: boolean;
  delayMs: number;
}

const FRAMES: ScriptFrame[] = [
  {
    lines: ["$ valkyrie", "Hey Sam. Ready. model: auto · ctx 4%"],
    delayMs: 1200,
  },
  {
    lines: ["$ valkyrie", "Hey Sam. Ready. model: auto · ctx 4%", "> /pl"],
    showAutocomplete: true,
    delayMs: 1300,
  },
  {
    lines: [
      "$ valkyrie",
      "Hey Sam. Ready. model: auto · ctx 4%",
      "> /plan add rate limiting to the FastAPI service",
    ],
    delayMs: 1100,
  },
  {
    lines: [
      "$ valkyrie",
      "Hey Sam. Ready. model: auto · ctx 4%",
      "> /plan add rate limiting to the FastAPI service",
      "  Plan · 4 steps",
      "  1  read app/main.py, app/deps.py",
      "  2  add rate-limit middleware",
      "  3  write tests/test_rate_limit.py",
      "  4  run pytest",
    ],
    delayMs: 1600,
  },
  {
    lines: [
      "$ valkyrie",
      "Hey Sam. Ready. model: auto · ctx 4%",
      "> /plan add rate limiting to the FastAPI service",
      "  Plan · 4 steps",
      "  1  read app/main.py, app/deps.py",
      "  2  add rate-limit middleware",
      "  3  write tests/test_rate_limit.py",
      "  4  run pytest",
      "Approve?  [a]pprove  [e]dit  [d]eny",
    ],
    delayMs: 3200,
  },
];

export function TerminalMock() {
  const [frameIdx, setFrameIdx] = useState(FRAMES.length - 1);
  const [tilt, setTilt] = useState({ rx: 6, ry: -12 });

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setFrameIdx(FRAMES.length - 1);
      setTilt({ rx: 0, ry: 0 });
      return;
    }

    setFrameIdx(0);
    let timer: ReturnType<typeof setTimeout>;
    let current = 0;

    const advance = () => {
      current = (current + 1) % FRAMES.length;
      setFrameIdx(current);
      timer = setTimeout(advance, FRAMES[current].delayMs);
    };

    timer = setTimeout(advance, FRAMES[0].delayMs);
    return () => clearTimeout(timer);
  }, []);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ rx: -ny * 6, ry: nx * 8 });
  };

  const handleMouseLeave = () => {
    setTilt({ rx: 6, ry: -12 });
    scrollStore.setState({ cursorMode: "default", cursorLabel: "" });
  };

  const frame = FRAMES[frameIdx];

  return (
    <div
      className="relative w-full max-w-[540px]"
      style={{ perspective: "1000px" }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => scrollStore.setState({ cursorMode: "view", cursorLabel: "View" })}
      onMouseLeave={handleMouseLeave}
    >
      {/* Screen-reader text alternative */}
      <p className="sr-only">
        Interactive terminal demonstration showing Valkyrie planning a four-step FastAPI rate
        limiting task and waiting for user approval.
      </p>

      <div
        className="vk-glass rounded-[20px] p-4 sm:p-5 shadow-soft transition-transform duration-300 ease-out"
        style={{
          transform: `rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)`,
        }}
      >
        {/* Window header with three hex dots */}
        <div className="mb-4 flex items-center justify-between border-b border-[rgba(242,244,241,0.10)] pb-3">
          <div className="flex items-center gap-2" aria-hidden="true">
            {[0, 1, 2].map((i) => (
              <svg key={i} width="11" height="11" viewBox="0 0 12 12" fill="none">
                <path
                  d="M6 1L10.5 3.5V8.5L6 11L1.5 8.5V3.5L6 1Z"
                  fill={i === 0 ? "#FFC929" : "#34373C"}
                  stroke="rgba(242,244,241,0.22)"
                  strokeWidth="0.9"
                />
              </svg>
            ))}
          </div>
          <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-[#A3A7AB]">
            valkyrie · zsh
          </span>
        </div>

        {/* Terminal body */}
        <div className="relative min-h-[218px] font-mono text-xs sm:text-[13px] leading-relaxed text-[#F2F4F1]">
          {frame.lines.map((line, i) => {
            const isPrompt = line.startsWith(">") || line.startsWith("$");
            const isApprove = line.startsWith("Approve?");
            const isPlanHeader = line.trim().startsWith("Plan");

            return (
              <div
                key={i}
                className={`whitespace-pre-wrap ${
                  isApprove
                    ? "mt-2 text-[#FFC929] font-medium"
                    : isPlanHeader
                    ? "mt-1 text-[#F2F4F1] font-medium"
                    : isPrompt
                    ? "text-[#F2F4F1]"
                    : "text-[#A3A7AB]"
                }`}
              >
                {line}
                {i === frame.lines.length - 1 && (
                  <span
                    className="ml-1 inline-block h-3.5 w-2 translate-y-[2px] bg-[#FFC929] animate-vk-blink"
                    aria-hidden="true"
                  />
                )}
              </div>
            );
          })}

          {/* Command autocomplete popup */}
          {frame.showAutocomplete && (
            <div className="mt-2 w-56 rounded-[12px] border border-[rgba(242,244,241,0.18)] bg-[#151619] p-2 shadow-soft">
              <div className="flex items-center justify-between rounded-md bg-[rgba(255,201,41,0.12)] px-2.5 py-1.5 text-xs">
                <span className="text-[#FFC929] font-medium">/plan</span>
                <span className="text-[#A3A7AB]">Create step plan</span>
              </div>
              <div className="flex items-center justify-between px-2.5 py-1.5 text-xs text-[#A3A7AB]">
                <span>/pkg</span>
                <span className="text-[#6F747A]">Manage packages</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


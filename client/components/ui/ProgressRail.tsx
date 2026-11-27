"use client";

import React from "react";
import { useScrollStore } from "@/lib/scroll-store";

export function ProgressRail() {
  const progress = useScrollStore((s) => s.progress);
  const section = useScrollStore((s) => s.section);

  const clampedSection = Math.min(Math.max(section + 1, 1), 6);
  const label = `0${clampedSection} / 06`;

  return (
    <aside
      aria-hidden="true"
      className="pointer-events-none fixed right-4 top-1/2 z-40 hidden -translate-y-1/2 flex-col items-center gap-3 md:flex lg:right-6"
    >
      <span className="font-mono text-[11px] tracking-[0.14em] text-[#A3A7AB] [writing-mode:vertical-rl]">
        {label}
      </span>
      <div className="relative h-32 w-[2px] overflow-hidden rounded-full bg-[rgba(242,244,241,0.12)]">
        <div
          className="absolute left-0 top-0 w-full rounded-full bg-[#FFC929] transition-[height] duration-150"
          style={{ height: `${Math.max(4, Math.min(100, progress * 100))}%` }}
        />
      </div>
    </aside>
  );
}


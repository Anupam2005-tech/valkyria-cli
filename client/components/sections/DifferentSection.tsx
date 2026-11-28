"use client";

import React, { useState } from "react";
import { COMPARISON_ROWS, DIFFERENT_STATS } from "@/lib/constants";
import { ScrollReveal } from "@/components/ui/ScrollReveal";

export function DifferentSection() {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const active = COMPARISON_ROWS[selectedIdx];

  return (
    <section
      id="different"
      aria-labelledby="different-heading"
      className="relative z-20 flex min-h-screen min-h-[100dvh] w-full items-center overflow-hidden feather-cut-both bg-[#F2F4F1] px-6 py-14 text-[#1C1D20] sm:px-8 sm:py-16"
    >
      {/* Static hairline grid background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(28, 29, 32, 0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(28, 29, 32, 0.06) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 mx-auto w-full max-w-[1280px]">
        {/* Asymmetric split header + stepped stat rail */}
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:items-end">
          <ScrollReveal className="lg:col-span-6 max-w-[600px]">
            <span className="type-label text-[#4A4E55] tabular-nums">
              02 · Why Valkyrie
            </span>
            <h2 id="different-heading" className="type-display-lg mt-3 text-[#1C1D20]">
              Not another chat box in a terminal{" "}
              <span className="relative inline-block text-[#1C1D20]">
                costume
                <svg
                  viewBox="0 0 180 12"
                  fill="none"
                  aria-hidden="true"
                  className="absolute -bottom-1 left-0 w-full h-2.5"
                >
                  <path
                    d="M2 9C48 3 125 2 178 7"
                    stroke="#FFC929"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
            </h2>
          </ScrollReveal>

          {/* 3 stepped stat blocks */}
          <ScrollReveal delay={0.12} className="lg:col-span-6 grid grid-cols-3 gap-3 sm:gap-4">
            {DIFFERENT_STATS.map((stat, idx) => (
              <div
                key={stat.label}
                className="rounded-[14px] border border-[#1C1D20]/14 bg-white/90 p-4 sm:p-5"
                style={{ marginTop: `${idx * 10}px` }}
              >
                <div className="font-mono text-2xl sm:text-4xl font-semibold tracking-tight tabular-nums text-[#1C1D20]">
                  {stat.value}
                </div>
                <div className="mt-1.5 text-xs sm:text-sm font-medium text-[#4A4E55]">
                  {stat.label}
                </div>
              </div>
            ))}
          </ScrollReveal>
        </div>

        {/* Unique Interactive Split Matrix: Selector rail left + Contrast stage right */}
        <div className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left selector rail */}
          <ScrollReveal delay={0.1} className="lg:col-span-5">
          <div role="tablist" aria-label="Valkyrie capabilities" className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-1">
            {COMPARISON_ROWS.map((row, idx) => {
              const isSelected = idx === selectedIdx;
              return (
                <button
                  key={row.feature}
                  role="tab"
                  type="button"
                  aria-selected={isSelected}
                  onClick={() => setSelectedIdx(idx)}
                  className={`flex items-center justify-between rounded-[12px] border px-4 py-3.5 text-left transition-colors min-h-[52px] ${
                    isSelected
                      ? "border-[#1C1D20] bg-[#1C1D20] text-[#F2F4F1]"
                      : "border-[#1C1D20]/14 bg-white/85 text-[#1C1D20] hover:border-[#1C1D20]/35"
                  }`}
                >
                  <span className="flex items-center gap-3">
                    <span
                      className={`font-mono text-xs tabular-nums ${
                        isSelected ? "text-[#FFC929]" : "text-[#9499A0]"
                      }`}
                    >
                      0{idx + 1}
                    </span>
                    <span className="font-display text-sm sm:text-base font-medium">
                      {row.feature}
                    </span>
                  </span>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                    className="shrink-0"
                  >
                    <path
                      d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z"
                      fill={isSelected ? "#FFC929" : "transparent"}
                      stroke={isSelected ? "#FFC929" : "rgba(28,29,32,0.28)"}
                      strokeWidth="1.4"
                    />
                  </svg>
                </button>
              );
            })}
          </div>
          </ScrollReveal>

          {/* Right split contrast stage */}
          <ScrollReveal delay={0.2} className="lg:col-span-7">
          <div
            role="tabpanel"
            className="grid grid-cols-1 gap-4 rounded-[20px] border border-[#1C1D20]/14 bg-white/95 p-6 sm:grid-cols-2 sm:p-8"
          >
            {/* Typical AI CLI card */}
            <div className="flex flex-col justify-between rounded-[14px] border border-[#1C1D20]/10 bg-[#F2F4F1]/75 p-5">
              <div>
                <span className="font-mono text-xs text-[#9499A0]">
                  Typical AI CLI
                </span>
                <p className="mt-4 font-display text-lg sm:text-xl font-medium text-[#1C1D20]/60 line-through decoration-[#1C1D20]/25">
                  {active.typical}
                </p>
              </div>
              <div className="mt-8 font-mono text-xs text-[#9499A0]">
                0{selectedIdx + 1} · {active.feature}
              </div>
            </div>

            {/* Valkyrie card */}
            <div className="flex flex-col justify-between rounded-[14px] bg-[#1C1D20] p-5 text-[#F2F4F1]">
              <div>
                <span className="inline-flex items-center gap-2 font-mono text-xs text-[#FFC929]">
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z" fill="#FFC929" />
                  </svg>
                  Valkyrie
                </span>
                <p className="mt-4 font-display text-lg sm:text-xl font-medium leading-snug text-[#F2F4F1]">
                  {active.valkyrie}
                </p>
              </div>
              <div className="mt-8 flex items-center justify-between border-t border-[rgba(242,244,241,0.10)] pt-3 font-mono text-xs text-[#A3A7AB]">
                <span>Verified in CLI</span>
                <span className="text-[#FFC929] tabular-nums">
                  0{selectedIdx + 1} / 0{COMPARISON_ROWS.length}
                </span>
              </div>
            </div>
          </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}

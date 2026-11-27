"use client";

import React from "react";
import Download8 from "@/components/ui/download-8";
import AsciiStream from "@/components/ui/ascii-stream";
import { ScrollReveal } from "@/components/ui/ScrollReveal";

export function SetupSection() {
  return (
    <section
      id="setup"
      aria-labelledby="setup-heading"
      className="relative z-10 overflow-hidden px-6 sm:px-8 py-14 sm:py-16"
    >
      {/* ASCII Stream ribbons backdrop */}
      <div className="pointer-events-none absolute inset-0 z-0">
        <AsciiStream
          colors={["#34373C", "#6F747A", "#FFC929", "#F2F4F1"]}
          ribbons={4}
          speed={0.6}
          cellSize={18}
          opacity={0.42}
        />
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-gradient-to-b from-[#101113] via-transparent to-[#101113]"
        />
      </div>

      <div className="relative z-10 mx-auto max-w-[1280px]">
        <ScrollReveal className="mx-auto max-w-[680px] text-center">
          <span className="type-label text-[#FFC929] tabular-nums">
            05 · Install Valkyrie
          </span>
          <h2 id="setup-heading" className="type-display-lg mt-3 text-[#F2F4F1]">
            Ready for{" "}
            <span className="text-[#FFC929]">takeoff</span>
          </h2>
          <p className="type-body-lg mt-4 text-[#A3A7AB]">
            Install the CLI in one command, bring your own API keys, and start
            shipping from your terminal.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.12} className="mt-12">
          <Download8 />
        </ScrollReveal>
      </div>
    </section>
  );
}

"use client";

import React from "react";
import { motion } from "framer-motion";
import { WobbleCard } from "@/components/ui/wobble-card";
import { ScrollReveal } from "@/components/ui/ScrollReveal";
import {
  CONTEXT_BUDGET_SEGMENTS,
  UNDER_THE_HOOD_PLATES,
} from "@/lib/constants";

// Asymmetric 10-column bento spans:
// Row 1: 70% + 30% | Row 2: 30% + 70% | Row 3: 50% + 50%
const BENTO_SPANS = [
  "col-span-1 lg:col-span-7 bg-[#151619]",
  "col-span-1 lg:col-span-3 bg-[#1C1D20]",
  "col-span-1 lg:col-span-3 bg-[#1C1D20]",
  "col-span-1 lg:col-span-7 bg-[#151619]",
  "col-span-1 lg:col-span-5 bg-[#151619]",
  "col-span-1 lg:col-span-5 bg-[#1C1D20]",
];

export function UnderTheHoodSection() {
  return (
    <section
      id="under-the-hood"
      aria-labelledby="hood-heading"
      className="relative z-10 px-6 sm:px-8 py-14 sm:py-16"
    >
      <div className="mx-auto max-w-[1280px]">
        <ScrollReveal className="max-w-[680px]">
          <span className="type-label text-[#FFC929] tabular-nums">
            03 · Under the hood
          </span>
          <h2 id="hood-heading" className="type-display-lg mt-3 text-[#F2F4F1]">
            Anatomy of a{" "}
            <span className="text-[#FFC929]">flight</span>
          </h2>
          <p className="type-body-lg mt-4 text-[#A3A7AB]">
            Six layered plates inside the shield. Every request passes through the
            same deterministic pipeline.
          </p>
        </ScrollReveal>

        {/* 10-column asymmetric bento grid: 70/30, 30/70, 50/50 */}
        <ScrollReveal delay={0.12} className="mt-12 grid grid-cols-1 gap-4 lg:grid-cols-10">
          {UNDER_THE_HOOD_PLATES.map((plate, idx) => (
            <WobbleCard
              key={plate.id}
              containerClassName={`${BENTO_SPANS[idx]} min-h-[200px]`}
              className="flex flex-col justify-between"
            >
              <div className="relative z-10">
                <div className="flex items-center justify-between">
                  <span className="type-label text-[#FFC929] tabular-nums">
                    {plate.label}
                  </span>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z"
                      stroke="#FFC929"
                      strokeOpacity="0.65"
                      strokeWidth="1.4"
                    />
                  </svg>
                </div>

                <h3 className="type-h3 mt-3 text-[#F2F4F1]">{plate.headline}</h3>

                <ul className="mt-4 space-y-2.5">
                  {plate.bullets.map((b) => (
                    <li
                      key={b}
                      className="flex items-start gap-2.5 text-sm leading-relaxed text-[#A3A7AB]"
                    >
                      <span
                        className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#FFC929]"
                        aria-hidden="true"
                      />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Context budget bar on Plate 5 */}
              {plate.showBudget && (
                <div className="relative z-10 mt-6 border-t border-[rgba(242,244,241,0.08)] pt-4">
                  <div className="mb-2 flex items-center justify-between font-mono text-[11px] text-[#A3A7AB]">
                    <span>Context budget</span>
                    <span className="text-[#FFC929] tabular-nums">
                      75% compact threshold
                    </span>
                  </div>
                  <div className="flex h-2 w-full overflow-hidden rounded-[4px] bg-[#101113]">
                    {CONTEXT_BUDGET_SEGMENTS.map((seg) => (
                      <motion.div
                        key={seg.label}
                        initial={{ width: 0 }}
                        whileInView={{ width: `${seg.pct}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
                        style={{ backgroundColor: seg.color }}
                        title={`${seg.label}: ${seg.pct}%`}
                      />
                    ))}
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-x-3 gap-y-1 font-mono text-[11px] text-[#9499A0]">
                    {CONTEXT_BUDGET_SEGMENTS.map((seg) => (
                      <span
                        key={seg.label}
                        className="inline-flex items-center gap-1.5"
                      >
                        <span
                          className="inline-block h-1.5 w-1.5 rounded-full"
                          style={{ backgroundColor: seg.color }}
                        />
                        {seg.label}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </WobbleCard>
          ))}
        </ScrollReveal>
      </div>
    </section>
  );
}

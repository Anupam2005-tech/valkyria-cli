"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function IntroLoader() {
  const [visible, setVisible] = useState(false);
  const [splitting, setSplitting] = useState(false);
  const [pct, setPct] = useState(0);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    try {
      if (sessionStorage.getItem("vk_intro_seen")) return;
      sessionStorage.setItem("vk_intro_seen", "1");
    } catch {
      return;
    }

    setVisible(true);

    const start = performance.now();
    const duration = 1250;
    let raf = 0;

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setPct(Math.round(eased * 100));
      if (t < 1) {
        raf = requestAnimationFrame(tick);
      }
    };
    raf = requestAnimationFrame(tick);

    const t1 = setTimeout(() => setSplitting(true), 1320);
    const t2 = setTimeout(() => setVisible(false), 1820);

    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);

  if (!visible) return null;

  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-[100] pointer-events-auto overflow-hidden"
        aria-label="Loading Valkyrie"
      >
        {/* Top split curtain */}
        <motion.div
          initial={{ y: 0 }}
          animate={{ y: splitting ? "-100%" : 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="absolute inset-x-0 top-0 h-1/2 bg-[#101113] border-b border-[rgba(242,244,241,0.06)]"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(242, 244, 241, 0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(242, 244, 241, 0.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        {/* Bottom split curtain */}
        <motion.div
          initial={{ y: 0 }}
          animate={{ y: splitting ? "100%" : 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="absolute inset-x-0 bottom-0 h-1/2 bg-[#101113]"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(242, 244, 241, 0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(242, 244, 241, 0.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        {/* Foreground content follows the landing page grid and gutters. */}
        <motion.div
          initial={{ opacity: 1 }}
          animate={{ opacity: splitting ? 0 : 1 }}
          transition={{ duration: 0.22 }}
          className="relative z-10 mx-auto flex h-full min-h-[100dvh] w-full max-w-[1280px] flex-col justify-between px-6 py-7 sm:px-8 sm:py-10"
        >
          <div className="flex items-center justify-between border-b border-[rgba(242,244,241,0.14)] pb-5">
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 bg-[#FFC929]" aria-hidden="true" />
              <span className="type-label uppercase tracking-[0.14em] text-[#F2F4F1]">
                Valkyrie / CLI
              </span>
            </div>
            <button
              type="button"
              onClick={() => setVisible(false)}
              className="type-label min-h-[44px] rounded-[6px] border border-[rgba(242,244,241,0.18)] px-4 py-2 text-[#F2F4F1] transition-colors hover:border-[#FFC929] hover:text-[#FFC929]"
            >
              Skip intro
            </button>
          </div>

          <div className="grid w-full items-center gap-8 py-8 sm:gap-10 lg:grid-cols-12">
            <div className="lg:col-span-8">
              <motion.p
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.15 }}
                className="type-label mb-5 uppercase tracking-[0.14em] text-[#FFC929]"
              >
                Terminal-native AI agent
              </motion.p>
              <motion.h2
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.65, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
                className="font-display text-[clamp(3.2rem,7.2vw,6.8rem)] font-bold leading-[0.95] tracking-[-0.055em] text-[#F2F4F1]"
              >
                Valkyrie<span className="text-[#FFC929]">.</span>
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, delay: 0.45 }}
                className="type-body-lg mt-6 max-w-[520px] text-[#A3A7AB]"
              >
                Your keys, your terminal, your rules.
              </motion.p>
            </div>

            <div className="relative flex min-h-[170px] items-center justify-center overflow-hidden border border-[rgba(242,244,241,0.14)] bg-[#151619] sm:min-h-[240px] lg:col-span-4">
              <span className="type-label absolute left-5 top-5 text-[#A3A7AB]">01 / AGENT</span>
              <svg
                width="112"
                height="112"
                viewBox="0 0 132 128"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
                className="h-24 w-24 sm:h-32 sm:w-32"
              >
                <motion.path
                  d="M24 20 66 106 108 20"
                  stroke="#F2F4F1"
                  strokeWidth="9"
                  strokeLinecap="square"
                  strokeLinejoin="miter"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                />
                <motion.path
                  d="M66 15v38"
                  stroke="#FFC929"
                  strokeWidth="5"
                  strokeLinecap="square"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: 0.35, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
                />
                <motion.path
                  d="m58 49 8 12 8-12"
                  stroke="#FFC929"
                  strokeWidth="4"
                  strokeLinecap="square"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.45, ease: [0.22, 1, 0.36, 1] }}
                />
              </svg>
              <span className="type-label absolute bottom-5 right-5 text-[#9499A0]">
                EST. 2026
              </span>
            </div>
          </div>

          <div className="w-full border-t border-[rgba(242,244,241,0.14)] pt-5">
            <div className="mb-4 flex items-end justify-between gap-4">
              <div>
                <span className="type-label uppercase tracking-[0.14em] text-[#FFC929]">
                  Opening the workspace
                </span>
                <p className="mt-1 text-xs text-[#A3A7AB]">Built to move from prompt to action.</p>
              </div>
              <span
                className="font-display text-3xl font-semibold tabular-nums text-[#F2F4F1] sm:text-4xl"
                aria-hidden="true"
              >
                {String(pct).padStart(3, "0")}%
              </span>
            </div>
            <div className="h-[3px] w-full overflow-hidden bg-[rgba(242,244,241,0.12)]">
              <div
                className="h-full bg-[#FFC929] transition-[width] duration-75"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

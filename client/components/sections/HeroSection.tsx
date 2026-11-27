"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { MagneticButton } from "@/components/ui/MagneticButton";
import { TerminalMock } from "@/components/ui/TerminalMock";
import GradientASCII from "@/components/ui/gradient-ascii";
import { PROVIDER_STRIP } from "@/lib/constants";

export function HeroSection() {
  return (
    <section
      id="hero"
      aria-labelledby="hero-heading"
      className="relative z-10 flex min-h-[82vh] flex-col justify-between overflow-hidden pt-24 pb-8 px-6 sm:px-8"
    >
      {/* Interactive GradientASCII hero backdrop */}
      <div className="pointer-events-none absolute inset-0 z-0 opacity-75">
        <GradientASCII
          colors={["#151619", "#34373C", "#FFC929", "#F2F4F1"]}
          shape="horizon"
          characters=" =+xX0S8#@"
          cellSize={18}
          density={0.8}
          glyphOpacity={0.85}
          gradientOpacity={0.85}
          glow={0.18}
          grain={0.06}
          className="pointer-events-auto"
        />
        {/* Subtle bottom fade into page background */}
        <div
          aria-hidden="true"
          className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#101113] to-transparent"
        />
      </div>

      <div className="relative z-10 mx-auto grid w-full max-w-[1280px] flex-1 grid-cols-1 items-center gap-12 lg:grid-cols-12">
        {/* Left copy column */}
        <div className="lg:col-span-7 max-w-[680px]">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="mb-6 inline-flex items-center gap-2 rounded-[8px] border border-[rgba(242,244,241,0.12)] bg-[#151619]/90 px-3 py-1.5"
          >
            <svg width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <path d="M6 1L10.5 3.5V8.5L6 11L1.5 8.5V3.5L6 1Z" fill="#FFC929" />
            </svg>
            <span className="type-label text-[#A3A7AB]">
              Terminal-native AI agent · Bring your own keys
            </span>
          </motion.div>

          <h1 id="hero-heading" className="type-display-xl text-[#F2F4F1]">
            <span className="block overflow-hidden">
              <motion.span
                className="block"
                initial={{ y: "105%" }}
                animate={{ y: 0 }}
                transition={{ duration: 0.75, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
              >
                Your terminal
              </motion.span>
            </span>
            <span className="block overflow-hidden">
              <motion.span
                className="block"
                initial={{ y: "105%" }}
                animate={{ y: 0 }}
                transition={{ duration: 0.75, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
              >
                grew <span className="text-[#FFC929]">wings</span>
              </motion.span>
            </span>
          </h1>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="type-body-lg mt-6 max-w-[560px] text-[#A3A7AB]"
          >
            Valkyrie plans, edits files, searches the web, and indexes codebases in
            Pinecone using your Groq, Gemini, and NVIDIA keys under explicit approval.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <MagneticButton href="/#setup">
              Get Valkyrie
              <ArrowUpRight className="h-4 w-4" strokeWidth={1.5} />
            </MagneticButton>
            <MagneticButton href="/docs" variant="ghost">
              Read the manual
            </MagneticButton>
          </motion.div>
        </div>

        {/* Right terminal mockup column */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="lg:col-span-5 flex justify-center lg:justify-end"
        >
          <TerminalMock />
        </motion.div>
      </div>

      {/* Bottom infinite right-to-left provider marquee */}
      <div className="relative z-10 mx-auto mt-14 flex w-full max-w-[1280px] flex-col gap-4 border-t border-[rgba(242,244,241,0.08)] pt-6 sm:flex-row sm:items-center sm:justify-between">
        <div
          className="relative flex-1 overflow-hidden"
          style={{
            maskImage:
              "linear-gradient(to right, transparent, black 8%, black 92%, transparent)",
            WebkitMaskImage:
              "linear-gradient(to right, transparent, black 8%, black 92%, transparent)",
          }}
        >
          <div className="animate-vk-marquee flex items-center gap-8 font-mono text-xs uppercase tracking-[0.12em] text-[#A3A7AB]">
            {[...PROVIDER_STRIP, ...PROVIDER_STRIP, ...PROVIDER_STRIP, ...PROVIDER_STRIP].map(
              (item, idx) => (
                <span key={idx} className="inline-flex items-center gap-8 whitespace-nowrap">
                  <span>{item}</span>
                  <svg width="8" height="8" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <path
                      d="M6 1L10.5 3.5V8.5L6 11L1.5 8.5V3.5L6 1Z"
                      stroke="#FFC929"
                      strokeOpacity="0.65"
                      strokeWidth="1.2"
                    />
                  </svg>
                </span>
              )
            )}
          </div>
        </div>

        <span className="type-label shrink-0 self-end text-[#A3A7AB] sm:self-auto" aria-hidden="true">
          Scroll to explore
        </span>
      </div>
    </section>
  );
}

"use client";

import React, { useEffect, useRef, useState } from "react";
import { Terminal, ListChecks, ShieldCheck, Hammer } from "lucide-react";
import BranchedMenu, { type BranchedMenuItem } from "@/components/ui/branched-menu";
import MagicRings from "@/components/ui/magic-rings";
import { ScrollReveal } from "@/components/ui/ScrollReveal";
import { HOW_IT_WORKS_STEPS } from "@/lib/constants";

const FLIGHT_MENU_ITEMS: BranchedMenuItem[] = [
  {
    label: "01 · Connect",
    children: [
      {
        value: "0",
        label: "valkyrie login",
        icon: <Terminal className="h-4 w-4" strokeWidth={1.5} />,
      },
    ],
  },
  {
    label: "02 · Plan",
    children: [
      {
        value: "1",
        label: "/plan migrate auth to JWT",
        icon: <ListChecks className="h-4 w-4" strokeWidth={1.5} />,
      },
    ],
  },
  {
    label: "03 · Approve",
    children: [
      {
        value: "2",
        label: "[a]pprove [e]dit [d]eny",
        icon: <ShieldCheck className="h-4 w-4" strokeWidth={1.5} />,
      },
    ],
  },
  {
    label: "04 · Build",
    children: [
      {
        value: "3",
        label: "/new · /session",
        icon: <Hammer className="h-4 w-4" strokeWidth={1.5} />,
      },
    ],
  },
];

export function HowItWorksSection() {
  const [activeStep, setActiveStep] = useState(0);
  const [manifestoProgress, setManifestoProgress] = useState(0);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onScroll = () => {
      const sec = sectionRef.current;
      if (!sec) return;
      const rect = sec.getBoundingClientRect();
      const vh = window.innerHeight;
      const manifesto = Math.max(0, Math.min(1, (vh * 0.85 - rect.top) / (vh * 0.55)));
      setManifestoProgress(manifesto);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const manifestoWords =
    "No prompt gymnastics. You say what you want, Valkyrie shows its plan, you approve, it builds.".split(
      " "
    );

  const current = HOW_IT_WORKS_STEPS[activeStep];

  return (
    <section
      id="how-it-works"
      ref={sectionRef}
      aria-labelledby="how-heading"
      className="relative z-10 overflow-hidden px-6 sm:px-8 py-14 sm:py-16"
    >
      {/* MagicRings interactive backdrop */}
      <div className="pointer-events-none absolute inset-0 z-0 opacity-60">
        <MagicRings
          color="#FFC929"
          colorTwo="#A3A7AB"
          motion="pulse"
          ringCount={4}
          speed={0.9}
          lineThickness={2}
          glow={0.65}
          hoverScale={1.12}
          clickBurst={true}
          opacity={0.75}
        />
      </div>

      <div className="relative z-10 mx-auto max-w-[1280px]">
        <ScrollReveal className="max-w-[680px]">
          <span className="type-label text-[#FFC929] tabular-nums">01 · The loop</span>
          <h2 id="how-heading" className="type-display-lg mt-3 text-[#F2F4F1]">
            Four moves, one{" "}
            <span className="text-[#FFC929]">flight path</span>
          </h2>

          {/* Scrubbed manifesto line */}
          <p className="type-body-lg mt-5 leading-relaxed">
            {manifestoWords.map((word, idx) => {
              const threshold = idx / manifestoWords.length;
              const lit = manifestoProgress >= threshold;
              return (
                <span
                  key={idx}
                  className="transition-opacity duration-200"
                  style={{
                    color: "#F2F4F1",
                    opacity: lit ? 1 : 0.3,
                  }}
                >
                  {word}{" "}
                </span>
              );
            })}
          </p>
        </ScrollReveal>

        <div className="mt-14 grid grid-cols-1 gap-10 lg:grid-cols-12">
          {/* Left: BranchedMenu navigation + active step card */}
          <ScrollReveal delay={0.1} className="lg:col-span-5 flex flex-col gap-6">
            <div className="rounded-[16px] border border-[rgba(242,244,241,0.10)] bg-[#151619]/95 p-6">
              <BranchedMenu
                items={FLIGHT_MENU_ITEMS}
                defaultOpen={[0, 1, 2, 3]}
                defaultActive="0"
                onSelect={(val) => setActiveStep(Number(val))}
                onToggle={(idx) => setActiveStep(idx)}
                color="#F2F4F1"
                accentColor="#FFC929"
                lineColor="#34373C"
                width={340}
                rowHeight={38}
                indent={40}
                trunk={14}
                radius={10}
                lineWidth={1.5}
                fontSize={14}
                drawDuration={400}
                foldDuration={300}
              />
            </div>

            <div className="rounded-[16px] border border-[rgba(255,201,41,0.40)] bg-[#151619]/95 p-6">
              <div className="flex items-baseline gap-4">
                <span className="font-mono text-2xl font-semibold tabular-nums text-[#FFC929]">
                  {current.num}
                </span>
                <div>
                  <h3 className="type-h3 text-[#F2F4F1]">{current.title}</h3>
                  <p className="mt-2 text-sm sm:text-base leading-relaxed text-[#A3A7AB]">
                    {current.copy}
                  </p>
                </div>
              </div>
            </div>
          </ScrollReveal>

          {/* Right: sticky terminal snippet */}
          <div className="lg:col-span-7">
            <div className="lg:sticky lg:top-28">
              <ScrollReveal delay={0.18}>
              <div className="rounded-[16px] border border-[rgba(242,244,241,0.10)] bg-[#151619]/95 p-6">
                <div className="mb-4 flex items-center justify-between border-b border-[rgba(242,244,241,0.08)] pb-3">
                  <span className="type-label text-[#FFC929] tabular-nums">
                    Step {current.num} · {current.title}
                  </span>
                  <span className="font-mono text-xs text-[#6F747A]">
                    Live transcript
                  </span>
                </div>

                <div className="min-h-[240px] space-y-2.5 font-mono text-xs sm:text-sm">
                  {current.snippet.map((line, i) => (
                    <div
                      key={`${current.num}-${i}`}
                      className={
                        line.startsWith("$") || line.startsWith(">")
                          ? "text-[#F2F4F1]"
                          : line.includes("Approve?") || line.includes("passed")
                          ? "text-[#FFC929]"
                          : "text-[#A3A7AB]"
                      }
                    >
                      {line}
                    </div>
                  ))}
                </div>
              </div>
              </ScrollReveal>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

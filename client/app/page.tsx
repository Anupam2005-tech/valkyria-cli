"use client";

import React, { useEffect } from "react";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { scrollStore } from "@/lib/scroll-store";
import { IntroLoader } from "@/components/ui/IntroLoader";
import { ProgressRail } from "@/components/ui/ProgressRail";
import { Navbar } from "@/components/nav/Navbar";
import { HeroSection } from "@/components/sections/HeroSection";
import { HowItWorksSection } from "@/components/sections/HowItWorksSection";
import { DifferentSection } from "@/components/sections/DifferentSection";
import { UnderTheHoodSection } from "@/components/sections/UnderTheHoodSection";
import { FaqSection } from "@/components/sections/FaqSection";
import { SetupSection } from "@/components/sections/SetupSection";
import { FooterSection } from "@/components/sections/FooterSection";

gsap.registerPlugin(ScrollTrigger);

const SECTION_IDS = [
  "hero",
  "how-it-works",
  "different",
  "under-the-hood",
  "faq",
  "setup",
  "footer",
];

export default function HomePage() {
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let lastY = window.scrollY;

    const updateScrollMetrics = (y: number, vel: number) => {
      const maxScroll = Math.max(
        1,
        document.documentElement.scrollHeight - window.innerHeight
      );
      const progress = Math.max(0, Math.min(1, y / maxScroll));
      const direction = y > lastY + 2 ? "down" : y < lastY - 2 ? "up" : scrollStore.getState().direction;
      lastY = y;

      let activeSection = 0;
      const anchor = window.innerHeight * 0.42;
      SECTION_IDS.forEach((id, idx) => {
        const el = document.getElementById(id);
        if (!el) return;
        const rect = el.getBoundingClientRect();
        if (rect.top <= anchor) {
          activeSection = idx;
        }
      });

      scrollStore.setState({
        progress,
        scrollY: y,
        velocity: vel,
        direction,
        section: activeSection,
      });
    };

    if (reduced) {
      const onNativeScroll = () => updateScrollMetrics(window.scrollY, 0);
      window.addEventListener("scroll", onNativeScroll, { passive: true });
      return () => window.removeEventListener("scroll", onNativeScroll);
    }

    const lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    lenis.on("scroll", (e: { scroll: number; velocity: number }) => {
      ScrollTrigger.update();
      updateScrollMetrics(e.scroll, e.velocity);
    });

    const tickerFn = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tickerFn);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tickerFn);
      lenis.destroy();
    };
  }, []);

  return (
    <>
      <IntroLoader />
      <ProgressRail />
      <Navbar />

      <main id="main-content" className="relative z-10">
        <HeroSection />
        <HowItWorksSection />
        <DifferentSection />
        <UnderTheHoodSection />
        <FaqSection />
        <SetupSection />
      </main>

      <FooterSection />
    </>
  );
}

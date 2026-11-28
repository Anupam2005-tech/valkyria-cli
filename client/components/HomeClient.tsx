"use client";

import React, { useEffect } from "react";
import dynamic from "next/dynamic";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { scrollStore } from "@/lib/scroll-store";
import { IntroLoader } from "@/components/ui/IntroLoader";
import { ProgressRail } from "@/components/ui/ProgressRail";
import { Navbar } from "@/components/nav/Navbar";
import { HeroSection } from "@/components/sections/HeroSection";

const HowItWorksSection = dynamic(
  () =>
    import("@/components/sections/HowItWorksSection").then(
      (mod) => mod.HowItWorksSection
    ),
  { ssr: true }
);

const DifferentSection = dynamic(
  () =>
    import("@/components/sections/DifferentSection").then(
      (mod) => mod.DifferentSection
    ),
  { ssr: true }
);

const UnderTheHoodSection = dynamic(
  () =>
    import("@/components/sections/UnderTheHoodSection").then(
      (mod) => mod.UnderTheHoodSection
    ),
  { ssr: true }
);

const FaqSection = dynamic(
  () => import("@/components/sections/FaqSection").then((mod) => mod.FaqSection),
  { ssr: true }
);

const SetupSection = dynamic(
  () =>
    import("@/components/sections/SetupSection").then(
      (mod) => mod.SetupSection
    ),
  { ssr: true }
);

const FooterSection = dynamic(
  () =>
    import("@/components/sections/FooterSection").then(
      (mod) => mod.FooterSection
    ),
  { ssr: true }
);

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

export function HomeClient() {
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let lastY = window.scrollY;
    let maxScroll = 1;
    let sectionTops: number[] = [];

    const measureLayout = () => {
      const vh = window.innerHeight;
      maxScroll = Math.max(1, document.documentElement.scrollHeight - vh);
      const scrollY = window.scrollY;
      sectionTops = SECTION_IDS.map((id) => {
        const el = document.getElementById(id);
        return el ? el.getBoundingClientRect().top + scrollY : Infinity;
      });
    };

    const updateScrollMetrics = (y: number, vel: number) => {
      const progress = Math.max(0, Math.min(1, y / maxScroll));
      const direction =
        y > lastY + 2
          ? "down"
          : y < lastY - 2
          ? "up"
          : scrollStore.getState().direction;
      lastY = y;

      let activeSection = 0;
      const anchor = y + window.innerHeight * 0.42;
      for (let idx = 0; idx < sectionTops.length; idx++) {
        if (sectionTops[idx] <= anchor) {
          activeSection = idx;
        }
      }

      scrollStore.setState({
        progress,
        scrollY: y,
        velocity: vel,
        direction,
        section: activeSection,
      });
    };

    measureLayout();
    const ro = new ResizeObserver(measureLayout);
    ro.observe(document.documentElement);
    window.addEventListener("resize", measureLayout, { passive: true });

    if (reduced) {
      let rafId = 0;
      const onNativeScroll = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          rafId = 0;
          updateScrollMetrics(window.scrollY, 0);
        });
      };
      window.addEventListener("scroll", onNativeScroll, { passive: true });
      return () => {
        if (rafId) cancelAnimationFrame(rafId);
        ro.disconnect();
        window.removeEventListener("resize", measureLayout);
        window.removeEventListener("scroll", onNativeScroll);
      };
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
      ro.disconnect();
      window.removeEventListener("resize", measureLayout);
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


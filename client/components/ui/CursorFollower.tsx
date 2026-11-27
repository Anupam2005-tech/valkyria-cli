"use client";

import React, { useEffect, useRef, useState } from "react";
import { useScrollStore } from "@/lib/scroll-store";

export function CursorFollower() {
  const [enabled, setEnabled] = useState(false);
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const cursorMode = useScrollStore((s) => s.cursorMode);
  const cursorLabel = useScrollStore((s) => s.cursorLabel);

  useEffect(() => {
    const isFine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!isFine || reduced) return;

    setEnabled(true);
    document.body.classList.add("has-custom-cursor");

    let mouseX = -100;
    let mouseY = -100;
    let ringX = -100;
    let ringY = -100;
    let rafId = 0;

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0)`;
      }
    };

    const tick = () => {
      ringX += (mouseX - ringX) * 0.16;
      ringY += (mouseY - ringY) * 0.16;
      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ringX}px, ${ringY}px, 0)`;
      }
      rafId = requestAnimationFrame(tick);
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    rafId = requestAnimationFrame(tick);

    return () => {
      document.body.classList.remove("has-custom-cursor");
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  if (!enabled) return null;

  const hasLabel = Boolean(cursorLabel);

  return (
    <div className="pointer-events-none fixed inset-0 z-[90] overflow-hidden" aria-hidden="true">
      {/* Leading yellow dot */}
      <div
        ref={dotRef}
        className="fixed left-0 top-0 -ml-1 -mt-1 h-2 w-2 rounded-full bg-[#FFC929] mix-blend-difference transition-opacity duration-150"
        style={{ opacity: hasLabel ? 0 : 1 }}
      />
      {/* Trailing ring / pill */}
      <div
        ref={ringRef}
        className={`fixed left-0 top-0 flex items-center justify-center rounded-full border transition-[width,height,margin,background-color,border-color] duration-200 mix-blend-difference ${
          hasLabel
            ? "-ml-8 -mt-4 h-8 w-16 border-[#FFC929] bg-[#FFC929] text-[#1C1D20]"
            : cursorMode !== "default"
            ? "-ml-5 -mt-5 h-10 w-10 border-[#FFC929]/80"
            : "-ml-4 -mt-4 h-8 w-8 border-[#F2F4F1]/45"
        }`}
      >
        {hasLabel && (
          <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-[#1C1D20]">
            {cursorLabel}
          </span>
        )}
      </div>
    </div>
  );
}


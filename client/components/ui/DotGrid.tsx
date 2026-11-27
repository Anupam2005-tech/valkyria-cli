"use client";

import React, { useEffect, useRef } from "react";

interface DotGridProps {
  dimmed?: boolean;
}

export function DotGrid({ dimmed = false }: DotGridProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let mouseX = -9999;
    let mouseY = -9999;
    let rafId = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      const gap = 36;
      const radius = 1;
      const baseAlpha = dimmed ? 0.06 : 0.11;
      const highlightRadius = 130;

      for (let x = gap / 2; x < w; x += gap) {
        for (let y = gap / 2; y < h; y += gap) {
          const dx = x - mouseX;
          const dy = y - mouseY;
          const dist = Math.hypot(dx, dy);

          if (!dimmed && !reduced && dist < highlightRadius) {
            const t = 1 - dist / highlightRadius;
            ctx.fillStyle = `rgba(255, 201, 41, ${0.14 + t * 0.45})`;
            ctx.beginPath();
            ctx.arc(x, y, radius + t * 0.8, 0, Math.PI * 2);
            ctx.fill();
          } else {
            ctx.fillStyle = `rgba(242, 244, 241, ${baseAlpha})`;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
    };

    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (!rafId) {
        rafId = requestAnimationFrame(() => {
          rafId = 0;
          draw();
        });
      }
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
    if (!reduced && !dimmed) {
      window.addEventListener("mousemove", onMove, { passive: true });
    }

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [dimmed]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0"
    />
  );
}

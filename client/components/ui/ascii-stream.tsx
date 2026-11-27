"use client";

import React, { useEffect, useRef } from "react";

export interface AsciiStreamProps {
  characters?: string;
  colors?: string[];
  ribbons?: number;
  speed?: number;
  cellSize?: number;
  opacity?: number;
  className?: string;
}

const DEFAULT_CHARS = ".:-=+*#%@01/\\";

export default function AsciiStream({
  characters = DEFAULT_CHARS,
  colors = ["#4A4E55", "#A3A7AB", "#FFC929", "#F2F4F1"],
  ribbons = 4,
  speed = 0.65,
  cellSize = 18,
  opacity = 0.48,
  className = "",
}: AsciiStreamProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 1;
    let h = 1;
    let dpr = 1;
    let raf = 0;
    let visible = true;
    let time = 0;
    let last = 0;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      w = Math.max(1, rect.width);
      h = Math.max(1, rect.height);
      dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const cols = Math.ceil(w / (cellSize * 0.68));
      const rows = Math.ceil(h / cellSize);

      ctx.font = `400 ${Math.round(cellSize * 0.78)}px "Geist Mono", ui-monospace, monospace`;
      ctx.textBaseline = "middle";
      ctx.textAlign = "center";

      for (let r = 0; r < rows; r++) {
        const ny = r / Math.max(1, rows - 1);
        for (let c = 0; c < cols; c++) {
          const nx = c / Math.max(1, cols - 1);

          // Sum influence across flowing sine ribbons
          let energy = 0;
          for (let k = 0; k < ribbons; k++) {
            const phase = k * 1.45 + time * (0.45 + k * 0.12);
            const ribbonY =
              0.5 +
              0.26 * Math.sin(nx * 4.2 + phase) +
              0.12 * Math.cos(nx * 7.5 - phase * 0.7);
            const dist = Math.abs(ny - ribbonY);
            const band = Math.exp(-(dist * dist) / 0.0085);
            if (band > energy) energy = band;
          }

          if (energy < 0.08) continue;

          // Flowing character stream along each ribbon
          const streamShift = Math.floor(time * 8 + c * 0.45 + r * 0.25);
          const charIdx = Math.min(
            characters.length - 1,
            Math.max(
              0,
              Math.floor(energy * (characters.length - 1)) + (streamShift % 2)
            )
          );
          const ch = characters[charIdx % characters.length];
          const colorIdx = Math.min(
            colors.length - 1,
            Math.floor(energy * (colors.length - 0.01))
          );

          ctx.globalAlpha = energy * opacity;
          ctx.fillStyle = colors[colorIdx];
          ctx.fillText(
            ch,
            c * cellSize * 0.68 + cellSize * 0.34,
            r * cellSize + cellSize * 0.5
          );
        }
      }
      ctx.globalAlpha = 1;
    };

    const tick = (now: number) => {
      raf = 0;
      if (!visible || document.hidden) return;
      const dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60;
      last = now;
      if (!reduced) time += dt * speed;
      draw();
      if (!reduced) raf = requestAnimationFrame(tick);
    };

    const ro = new ResizeObserver(() => {
      resize();
      draw();
    });
    ro.observe(container);

    const io = new IntersectionObserver((entries) => {
      visible = entries.some((e) => e.isIntersecting);
      if (visible && !raf && !reduced) {
        last = 0;
        raf = requestAnimationFrame(tick);
      }
    });
    io.observe(container);

    resize();
    draw();
    if (!reduced) raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
    };
  }, [characters, colors, ribbons, speed, cellSize, opacity]);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className={`pointer-events-none relative h-full w-full overflow-hidden ${className}`.trim()}
    >
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}


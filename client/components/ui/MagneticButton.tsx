"use client";

import React, { useRef, useState } from "react";
import Link from "next/link";
import { scrollStore } from "@/lib/scroll-store";

interface MagneticButtonProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: "primary" | "ghost";
  className?: string;
  cursorLabel?: string;
  type?: "button" | "submit";
}

export function MagneticButton({
  children,
  href,
  onClick,
  variant = "primary",
  className = "",
  cursorLabel = "View",
  type = "button",
}: MagneticButtonProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;
    const dist = Math.hypot(dx, dy);
    if (dist < 72) {
      setOffset({ x: dx * 0.18, y: dy * 0.18 });
    }
  };

  const handleMouseEnter = () => {
    scrollStore.setState({ cursorMode: "link", cursorLabel });
  };

  const handleMouseLeave = () => {
    setOffset({ x: 0, y: 0 });
    scrollStore.setState({ cursorMode: "default", cursorLabel: "" });
  };

  const baseStyles =
    variant === "primary"
      ? "bg-[#FFC929] text-[#1C1D20] font-medium hover:bg-[#FFD34E] active:scale-[0.98]"
      : "border border-[rgba(242,244,241,0.16)] text-[#F2F4F1] bg-transparent hover:border-[rgba(242,244,241,0.32)] hover:bg-[rgba(242,244,241,0.04)] active:scale-[0.98]";

  const innerClass = `inline-flex items-center justify-center gap-2 rounded-[10px] px-5 py-2.5 text-sm transition-[background-color,border-color,transform] duration-200 min-h-[44px] ${baseStyles} ${className}`;

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`,
        transition:
          offset.x === 0 && offset.y === 0
            ? "transform 0.35s cubic-bezier(0.22, 1, 0.36, 1)"
            : "transform 0.08s linear",
      }}
      className="inline-block"
    >
      {href ? (
        <Link href={href} className={innerClass}>
          {children}
        </Link>
      ) : (
        <button type={type} onClick={onClick} className={innerClass}>
          {children}
        </button>
      )}
    </div>
  );
}

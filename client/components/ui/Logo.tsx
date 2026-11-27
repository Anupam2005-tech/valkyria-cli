"use client";

import React from "react";

interface LogoProps {
  size?: number;
  className?: string;
}

export function Logo({ size = 28, className = "" }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 132 128"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Split-spear V */}
      <path
        d="M24 20 66 106 108 20"
        stroke="currentColor"
        strokeWidth="9"
        strokeLinecap="square"
        strokeLinejoin="miter"
      />
      {/* Directional yellow point */}
      <path
        d="M66 15v38"
        stroke="#FFC929"
        strokeWidth="5"
        strokeLinecap="square"
      />
      <path
        d="m58 49 8 12 8-12"
        stroke="#FFC929"
        strokeWidth="4"
        strokeLinecap="square"
      />
    </svg>
  );
}

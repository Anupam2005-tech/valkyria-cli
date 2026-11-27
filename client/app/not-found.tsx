import React from "react";
import { Navbar } from "@/components/nav/Navbar";
import { FooterSection } from "@/components/sections/FooterSection";
import { DotGrid } from "@/components/ui/DotGrid";
import { MagneticButton } from "@/components/ui/MagneticButton";

export default function NotFound() {
  return (
    <>
      <DotGrid dimmed />
      <Navbar solid />
      <main className="relative z-10 flex min-h-[82vh] flex-col items-center justify-center px-6 pt-28 pb-20 text-center">
        {/* Shield with a cracked wing */}
        <svg
          width="112"
          height="112"
          viewBox="0 0 80 80"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
          className="mb-8"
        >
          {/* Left wing */}
          <path
            d="M27 33L7 21L18 39L7 47L25 48"
            stroke="#F2F4F1"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Cracked right wing */}
          <path
            d="M53 33L71 22L63 34"
            stroke="#F2F4F1"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M60 40L72 47L55 48"
            stroke="#FFC929"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="3 3"
          />
          {/* Hexagon shield */}
          <path
            d="M40 12L58 23V45L40 64L22 45V23L40 12Z"
            stroke="#F2F4F1"
            strokeWidth="2.6"
            strokeLinejoin="round"
          />
          <path d="M40 28L45 36L40 46L35 36L40 28Z" fill="#FFC929" />
        </svg>

        <span className="type-label text-[#FFC929]">404 · Off course</span>
        <h1 className="type-display-lg mt-3 text-[#F2F4F1]">
          Even Valkyries get{" "}
          <span className="font-accent-word text-[#FFC929]">lost.</span>
        </h1>
        <p className="type-body-lg mt-4 max-w-[440px] text-[#A3A7AB]">
          That route does not exist. Head back to base and pick up the flight path.
        </p>
        <div className="mt-8">
          <MagneticButton href="/">Back to base</MagneticButton>
        </div>
      </main>
      <FooterSection />
    </>
  );
}


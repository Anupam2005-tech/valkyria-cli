"use client";

import React from "react";
import HalftoneWordmarkFooter, {
  type FooterColumn,
} from "@/components/ui/halftone-wordmark-footer";

const VALKYRIE_FOOTER_COLUMNS: FooterColumn[] = [
  {
    title: "Product",
    links: [
      { label: "How it works", href: "/#how-it-works" },
      { label: "Why Valkyrie", href: "/#different" },
      { label: "Setup", href: "/#setup" },
      { label: "FAQ", href: "/#faq" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Docs", href: "/docs" },
      { label: "Command reference", href: "/docs#commands-reference" },
      { label: "GitHub", href: "https://github.com/Anupam2005-tech/valkyria-cli" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Terms & Conditions", href: "/terms" },
      { label: "Privacy Policy", href: "/privacy" },
    ],
  },
];

export function FooterSection() {
  return (
    <div id="footer" className="relative z-10 w-full border-t border-[rgba(242,244,241,0.08)]">
      <HalftoneWordmarkFooter
        wordmark="valkyrie"
        label="Valkyrie"
        meta={`© ${new Date().getFullYear()} · Built with love and passion--Anupam, flown everywhere`}
        columns={VALKYRIE_FOOTER_COLUMNS}
        palette={{
          background: "#101113",
          ink: "#F2F4F1",
          warm: "#FFC929",
        }}
        fontFamily='"Bricolage Grotesque", "Geist", system-ui, sans-serif'
        fontWeight={600}
        monoFamily='"Geist Mono", ui-monospace, "SF Mono", monospace'
        height="500px"
        grain={0.35}
      />
    </div>
  );
}

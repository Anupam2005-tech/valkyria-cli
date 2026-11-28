import React from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { SiteHeader } from "@/components/ui/SiteHeader";
import { FooterSection } from "@/components/sections/FooterSection";
import { Logo } from "@/components/ui/Logo";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#101113] text-[#F2F4F1] selection:bg-[#FFC929] selection:text-[#101113]">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.24]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(242, 244, 241, 0.14) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      <SiteHeader sectionLabel="/ 404" />

      <main className="relative z-10 mx-auto flex min-h-[68vh] max-w-[1380px] flex-col items-center justify-center px-5 py-20 text-center sm:px-8">
        <div className="opacity-85">
          <Logo size={56} />
        </div>
        <span className="mt-6 font-[family-name:var(--font-mono)] text-xs uppercase tracking-[0.14em] text-[#FFC929]">
          Error 404
        </span>
        <h1 className="mt-3 text-[clamp(32px,4.5vw,52px)] font-semibold tracking-[-0.03em] text-[#F2F4F1]">
          Off the flight{" "}
          <span className="font-[family-name:var(--font-accent)] font-normal italic text-[#FFC929]">
            path.
          </span>
        </h1>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-[#9499A0]">
          That route does not exist. Head back to base or open the documentation.
        </p>

        <div className="mt-7 flex items-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 border border-white/20 px-4 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to base
          </Link>
          <Link
            href="/docs"
            className="inline-flex items-center border border-white/20 px-4 py-2 font-[family-name:var(--font-mono)] text-xs font-medium text-[#9499A0] transition hover:border-white/40 hover:text-[#F2F4F1]"
          >
            Read docs
          </Link>
        </div>
      </main>

      <FooterSection />
    </div>
  );
}

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Github, Menu, X } from "lucide-react";
import { Logo } from "@/components/ui/Logo";

const GITHUB_URL = "https://github.com/Anupam2005-tech/valkyria-cli";

export function SiteHeader({ sectionLabel }: { sectionLabel?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#101113]/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1380px] items-center justify-between px-5 sm:px-8">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-2.5 text-[#F2F4F1] transition-opacity hover:opacity-90"
          >
            <Logo size={24} />
            <span className="font-[family-name:var(--font-mono)] text-sm font-semibold tracking-tight">
              valkyria
            </span>
          </Link>
          {sectionLabel && (
            <span className="hidden font-[family-name:var(--font-mono)] text-xs text-[#6F747A] sm:inline">
              {sectionLabel}
            </span>
          )}
        </div>

        <nav className="hidden items-center gap-6 md:flex">
          <Link
            href="/"
            className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
          >
            Overview
          </Link>
          <Link
            href="/docs"
            className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
          >
            Docs
          </Link>
          <Link
            href="/#changelog"
            className="font-[family-name:var(--font-mono)] text-xs text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
          >
            Changelog
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            aria-label="Valkyria on GitHub"
            className="text-[#9499A0] transition-colors hover:text-[#F2F4F1]"
          >
            <Github className="h-4 w-4" />
          </a>
          <Link
            href="/#get-started"
            className="inline-flex items-center border border-white/20 px-3 py-1 font-[family-name:var(--font-mono)] text-xs font-medium text-[#F2F4F1] transition hover:border-[#FFC929] hover:text-[#FFC929]"
          >
            Install
          </Link>
        </nav>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle navigation"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-white/10 text-[#F2F4F1] md:hidden"
        >
          {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-white/[0.07] bg-[#101113] px-5 py-4 md:hidden">
          <div className="flex flex-col gap-3 font-[family-name:var(--font-mono)] text-xs">
            <Link href="/" onClick={() => setOpen(false)} className="text-[#9499A0] hover:text-[#F2F4F1]">
              Overview
            </Link>
            <Link href="/docs" onClick={() => setOpen(false)} className="text-[#9499A0] hover:text-[#F2F4F1]">
              Docs
            </Link>
            <Link href="/privacy" onClick={() => setOpen(false)} className="text-[#9499A0] hover:text-[#F2F4F1]">
              Privacy Policy
            </Link>
            <Link href="/terms" onClick={() => setOpen(false)} className="text-[#9499A0] hover:text-[#F2F4F1]">
              Terms &amp; Conditions
            </Link>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              className="text-[#9499A0] hover:text-[#F2F4F1]"
            >
              GitHub
            </a>
          </div>
        </div>
      )}
    </header>
  );
}


"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ChevronDown, Star } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Logo } from "@/components/ui/Logo";
import { useScrollStore } from "@/lib/scroll-store";

interface NavbarProps {
  solid?: boolean;
}

const CENTER_LINKS = [
  { label: "How it works", href: "/#how-it-works", section: 1 },
  { label: "Why Valkyrie", href: "/#different", section: 2 },
];

const PROTOCOL_ITEMS = [
  {
    label: "Docs",
    desc: "Command reference, architecture, and RAG setup",
    href: "/docs",
  },
  {
    label: "Setup guide",
    desc: "Install Valkyrie and run your first build",
    href: "/#setup",
  },
  {
    label: "FAQ",
    desc: "Keys, security, providers, and sessions",
    href: "/#faq",
  },
];

const GITHUB_REPO_URL = "https://github.com/Anupam2005-tech/valkyria-cli";

export function Navbar({ solid = false }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [protocolOpen, setProtocolOpen] = useState(false);
  const scrollY = useScrollStore((s) => s.scrollY);
  const activeSection = useScrollStore((s) => s.section);

  const scrolled = solid || scrollY > 24;

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMobileOpen(false);
        setProtocolOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <>
      <header
        className={`fixed inset-x-0 top-0 z-50 transition-[background-color,border-color] duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
          scrolled
            ? "bg-[#101113]/92 backdrop-blur-md border-b border-[rgba(242,244,241,0.10)]"
            : "bg-transparent border-b border-transparent"
        }`}
      >
        <nav
          aria-label="Primary navigation"
          className="mx-auto grid h-16 max-w-[1280px] grid-cols-2 min-[821px]:grid-cols-3 items-center px-6 sm:px-8"
        >
          {/* Left: Brand */}
          <div className="justify-self-start">
            <Link
              href="/"
              className="flex items-center gap-2.5 text-[#F2F4F1] hover:opacity-85 transition-opacity"
            >
              <Logo size={24} />
              <span className="font-display text-base font-semibold tracking-tight text-[#F2F4F1]">
                Valkyrie
              </span>
            </Link>
          </div>

          {/* Center: 3 options centered */}
          <ul className="hidden min-[821px]:flex items-center justify-center gap-8 justify-self-center">
            {CENTER_LINKS.map((item) => {
              const isActive = !solid && item.section === activeSection;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`inline-flex items-center gap-1.5 py-1 text-[13px] font-medium transition-colors ${
                      isActive
                        ? "text-[#F2F4F1]"
                        : "text-[#F2F4F1]/75 hover:text-[#F2F4F1]"
                    }`}
                  >
                    {isActive && (
                      <span
                        aria-hidden="true"
                        className="h-1.5 w-1.5 bg-[#FFC929]"
                      />
                    )}
                    {item.label}
                  </Link>
                </li>
              );
            })}

            {/* Protocol hover dropdown */}
            <li
              className="relative"
              onMouseEnter={() => setProtocolOpen(true)}
              onMouseLeave={() => setProtocolOpen(false)}
            >
              <button
                type="button"
                aria-expanded={protocolOpen}
                aria-haspopup="menu"
                onClick={() => setProtocolOpen((v) => !v)}
                className="inline-flex items-center gap-1 py-2 text-[13px] font-medium text-[#F2F4F1]/75 hover:text-[#F2F4F1] transition-colors"
              >
                <span>Protocol</span>
                <ChevronDown
                  className={`h-3.5 w-3.5 transition-transform duration-200 ${
                    protocolOpen ? "rotate-180 text-[#FFC929]" : ""
                  }`}
                  strokeWidth={1.75}
                />
              </button>

              <AnimatePresence>
                {protocolOpen && (
                  <motion.div
                    role="menu"
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 4 }}
                    transition={{ duration: 0.16, ease: [0.22, 1, 0.36, 1] }}
                    className="absolute left-1/2 top-full w-72 -translate-x-1/2 pt-2"
                  >
                    <div className="rounded-[10px] border border-[rgba(242,244,241,0.12)] bg-[#151619] p-2 shadow-[0_18px_40px_rgba(0,0,0,0.45)]">
                      {PROTOCOL_ITEMS.map((sub) => (
                        <Link
                          key={sub.href}
                          role="menuitem"
                          href={sub.href}
                          onClick={() => setProtocolOpen(false)}
                          className="block rounded-[8px] px-3 py-2.5 transition-colors hover:bg-[#26282C]"
                        >
                          <div className="text-[13px] font-medium text-[#F2F4F1]">
                            {sub.label}
                          </div>
                          <div className="mt-0.5 text-xs text-[#A3A7AB]">
                            {sub.desc}
                          </div>
                        </Link>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </li>
          </ul>

          {/* Right: GitHub Star CTA + Mobile burger */}
          <div className="flex items-center gap-3 justify-self-end">
            <a
              href={GITHUB_REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="hidden min-[821px]:inline-flex items-center gap-2 rounded-[4px] border border-[rgba(242,244,241,0.16)] bg-[#151619] px-4 py-2 text-[13px] font-medium text-[#F2F4F1] hover:border-[rgba(242,244,241,0.32)] hover:bg-[#1C1D20] transition-colors min-h-[38px]"
            >
              <Star
                className="h-3.5 w-3.5 text-[#FFC929]"
                fill="#FFC929"
                strokeWidth={1.5}
              />
              <span>Star on GitHub</span>
            </a>

            <button
              type="button"
              onClick={() => setMobileOpen((v) => !v)}
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileOpen}
              className="group relative flex h-11 w-11 items-center justify-center bg-transparent text-[#F2F4F1] transition-colors min-[821px]:hidden"
            >
              <span className="relative flex h-3.5 w-5 flex-col justify-between" aria-hidden="true">
                <span
                  className={`block h-[1.5px] w-full rounded-full bg-[#F2F4F1] transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                    mobileOpen ? "translate-y-[6px] rotate-45 bg-[#FFC929]" : ""
                  }`}
                />
                <span
                  className={`block h-[1.5px] rounded-full bg-[#FFC929] transition-[width,opacity] duration-150 ${
                    mobileOpen ? "w-0 opacity-0" : "w-3.5 opacity-100 self-end"
                  }`}
                />
                <span
                  className={`block h-[1.5px] w-full rounded-full bg-[#F2F4F1] transition-transform duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                    mobileOpen ? "-translate-y-[6px] -rotate-45" : ""
                  }`}
                />
              </span>
            </button>
          </div>
        </nav>
      </header>

      {/* Mobile full-screen drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 top-16 z-[70] flex flex-col justify-between bg-[#101113] px-6 py-8 text-[#F2F4F1] min-[821px]:hidden"
          >
            <ul className="divide-y divide-[rgba(242,244,241,0.08)] border-y border-[rgba(242,244,241,0.08)]">
              {[...CENTER_LINKS, ...PROTOCOL_ITEMS].map((item, idx) => (
                <motion.li
                  key={item.href}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    delay: 0.03 * idx,
                    duration: 0.25,
                    ease: [0.22, 1, 0.36, 1],
                  }}
                >
                  <Link
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center justify-between py-4 font-display text-2xl font-medium tracking-tight text-[#F2F4F1] hover:text-[#FFC929] transition-colors"
                  >
                    <span>{item.label}</span>
                    <ArrowRight className="h-4 w-4 text-[#6F747A]" strokeWidth={1.5} />
                  </Link>
                </motion.li>
              ))}
            </ul>

            <div className="pt-6">
              <a
                href={GITHUB_REPO_URL}
                target="_blank"
                rel="noreferrer"
                onClick={() => setMobileOpen(false)}
                className="flex w-full items-center justify-center gap-2 rounded-[4px] border border-[rgba(242,244,241,0.16)] bg-[#151619] py-3.5 text-sm font-medium text-[#F2F4F1] min-h-[44px]"
              >
                <Star className="h-4 w-4 text-[#FFC929]" fill="#FFC929" strokeWidth={1.5} />
                <span>Star on GitHub</span>
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

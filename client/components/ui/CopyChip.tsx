"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";
import { scrollStore } from "@/lib/scroll-store";

interface CopyChipProps {
  command: string;
  className?: string;
  prefix?: string;
}

export function CopyChip({ command, className = "", prefix = "$" }: CopyChipProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      // ignore
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      onMouseEnter={() => scrollStore.setState({ cursorMode: "copy", cursorLabel: "Copy" })}
      onMouseLeave={() => scrollStore.setState({ cursorMode: "default", cursorLabel: "" })}
      aria-label={`Copy command ${command}`}
      className={`group inline-flex items-center gap-3 rounded-[10px] border border-[rgba(242,244,241,0.12)] bg-[#151619] px-4 py-2 font-mono text-xs sm:text-sm text-[#F2F4F1] transition-colors duration-200 hover:border-[rgba(242,244,241,0.24)] min-h-[44px] ${className}`}
    >
      {prefix && <span className="text-[#FFC929] select-none">{prefix}</span>}
      <span>{command}</span>
      <span className="ml-1 inline-flex items-center gap-1.5 rounded-[6px] bg-[#26282C] px-2 py-1 text-[11px] text-[#A3A7AB] group-hover:text-[#F2F4F1] transition-colors">
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-[#FFC929]" strokeWidth={1.5} />
            <span className="text-[#FFC929]">Copied</span>
          </>
        ) : (
          <>
            <Copy className="h-3.5 w-3.5" strokeWidth={1.5} />
            <span>Copy</span>
          </>
        )}
      </span>
    </button>
  );
}



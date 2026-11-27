"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { CopyChip } from "@/components/ui/CopyChip";
import { cn } from "@/lib/utils";

export interface CraftCardItem {
  num: string;
  title: string;
  command: string;
  note: string;
}

interface InterfaceCraftsCardsProps {
  items: CraftCardItem[];
  className?: string;
  showCopy?: boolean;
}

export function InterfaceCraftsCards({
  items,
  className = "",
  showCopy = true,
}: InterfaceCraftsCardsProps) {
  const [activeIdx, setActiveIdx] = useState(0);

  return (
    <div className={cn("grid grid-cols-1 gap-3 lg:grid-cols-12", className)}>
      {items.map((item, idx) => {
        const isActive = idx === activeIdx;
        return (
          <motion.div
            key={item.num}
            layout
            onClick={() => setActiveIdx(idx)}
            onMouseEnter={() => setActiveIdx(idx)}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              "group relative cursor-pointer overflow-hidden rounded-[16px] border p-6 transition-colors",
              isActive
                ? "lg:col-span-4 border-[rgba(255,201,41,0.45)] bg-[#151619]"
                : "lg:col-span-2 border-[rgba(242,244,241,0.10)] bg-[#151619]/65 hover:border-[rgba(242,244,241,0.22)]"
            )}
          >
            <div className="flex h-full min-h-[220px] flex-col justify-between gap-6">
              <div>
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "font-mono text-xs tabular-nums transition-colors",
                      isActive ? "text-[#FFC929]" : "text-[#6F747A]"
                    )}
                  >
                    Step {item.num}
                  </span>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z"
                      fill={isActive ? "#FFC929" : "transparent"}
                      stroke={isActive ? "#FFC929" : "rgba(242,244,241,0.24)"}
                      strokeWidth="1.4"
                    />
                  </svg>
                </div>

                <h3 className="mt-4 font-display text-xl font-medium tracking-tight text-[#F2F4F1]">
                  {item.title}
                </h3>

                {isActive && (
                  <motion.p
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.22 }}
                    className="mt-2.5 text-sm leading-relaxed text-[#A3A7AB]"
                  >
                    {item.note}
                  </motion.p>
                )}
              </div>

              <div>
                {isActive && showCopy ? (
                  <CopyChip
                    command={item.command}
                    prefix={item.command.startsWith("/") ? "" : "$"}
                    className="w-full justify-between"
                  />
                ) : (
                  <div className="truncate font-mono text-xs text-[#6F747A]">
                    {item.command}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}


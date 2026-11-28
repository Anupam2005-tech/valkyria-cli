"use client";

import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
} from "framer-motion";
import React, { useEffect, useRef, useState } from "react";

export interface TimelineEntry {
  title: string;
  content: React.ReactNode;
}

export const Timeline = ({
  data,
  hideHeader = false,
  heading = "Changelog from the flight deck",
  subheading = "Every shipped release of Valkyria CLI—from multi-provider streaming to sandboxed execution.",
}: {
  data: TimelineEntry[];
  hideHeader?: boolean;
  heading?: string;
  subheading?: string;
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const measure = () => {
      setHeight(el.getBoundingClientRect().height);
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    window.addEventListener("resize", measure, { passive: true });
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [data]);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start 20%", "end 70%"],
  });

  const heightTransform = useTransform(scrollYProgress, [0, 1], [0, height]);
  const opacityTransform = useTransform(scrollYProgress, [0, 0.08], [0, 1]);

  return (
    <div
      className="w-full bg-transparent font-sans text-[#F2F4F1]"
      ref={containerRef}
    >
      {!hideHeader && (
        <div className="mx-auto max-w-7xl px-4 py-16 md:px-8 lg:px-10">
          <h2 className="mb-3 max-w-4xl text-xl font-semibold tracking-tight text-[#F2F4F1] md:text-4xl">
            {heading}
          </h2>
          <p className="max-w-md text-sm text-[#9499A0] md:text-base">
            {subheading}
          </p>
        </div>
      )}

      <div ref={ref} className="relative mx-auto pb-10">
        {data.map((item, index) => (
          <div
            key={index}
            className={`flex justify-start md:gap-10 ${
              index === 0 ? "pt-2" : "pt-12 md:pt-24"
            }`}
          >
            <div className="sticky top-28 z-20 flex max-w-xs flex-col items-center self-start md:w-56 md:flex-row lg:w-64">
              <div className="absolute left-3 flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-[#101113]">
                <div className="h-3 w-3 rounded-full border border-[#FFC929]/50 bg-[#1A1C21]" />
              </div>
              <h3 className="hidden pl-14 font-[family-name:var(--font-mono)] text-2xl font-bold tracking-tight text-[#A3A7AB] md:block md:text-3xl">
                {item.title}
              </h3>
            </div>

            <div className="relative w-full pl-14 pr-2 md:pl-0">
              <h3 className="mb-3 block text-left font-[family-name:var(--font-mono)] text-xl font-bold text-[#F2F4F1] md:hidden">
                {item.title}
              </h3>
              {item.content}
            </div>
          </div>
        ))}

        <div
          style={{
            height: height + "px",
          }}
          className="absolute left-[27px] top-0 w-[2px] overflow-hidden bg-[linear-gradient(to_bottom,var(--tw-gradient-stops))] from-transparent from-[0%] via-white/15 to-transparent to-[99%] [mask-image:linear-gradient(to_bottom,transparent_0%,black_10%,black_90%,transparent_100%)]"
        >
          {prefersReducedMotion ? (
            <div className="absolute inset-x-0 top-0 h-full w-[2px] rounded-full bg-gradient-to-t from-[#FFC929] via-[#FFC929]/60 to-transparent" />
          ) : (
            <motion.div
              style={{
                height: heightTransform,
                opacity: opacityTransform,
              }}
              className="absolute inset-x-0 top-0 w-[2px] rounded-full bg-gradient-to-t from-[#FFC929] via-[#FFC929]/75 to-transparent from-[0%] via-[15%]"
            />
          )}
        </div>
      </div>
    </div>
  );
};

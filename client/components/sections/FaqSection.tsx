"use client";

import React from "react";
import { FaqDrawer, type FaqDrawerCard } from "@/components/ui/faq-drawer";
import { ScrollReveal } from "@/components/ui/ScrollReveal";
import { FAQ_ITEMS } from "@/lib/constants";

const TABS = ["Offline", "Keys", "Models", "Safety", "Pinecone", "Pricing", "Systems"];

const VALKYRIE_FAQ_CARDS: FaqDrawerCard[] = FAQ_ITEMS.slice(0, 7).map((item, idx) => ({
  id: `vk-faq-${idx}`,
  tab: TABS[idx] || "General",
  q: item.q,
  a: item.a,
}));

export function FaqSection() {
  return (
    <div id="faq" className="relative z-10 w-full">
      <ScrollReveal>
      <FaqDrawer
        label="04 · FAQ"
        title="Questions, answered"
        lead="Straight answers on keys, security, providers and how Valkyrie handles your machine."
        drawer="Valkyrie · Q–Z"
        cards={VALKYRIE_FAQ_CARDS}
        count={7}
        open="1"
        single={true}
        askNote="Need more detail? Read the full command and architecture manual."
        askLabel="Read docs"
        askHref="/docs"
        finish="graphite"
      />
      </ScrollReveal>
    </div>
  );
}

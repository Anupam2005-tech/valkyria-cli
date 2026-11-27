import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "Documentation & Command Reference",
  description:
    "Complete user manual for Valkyrie CLI: installation, slash commands, Pinecone RAG indexing, Groq/Gemini/NVIDIA model switching, and encrypted vault sync.",
  alternates: {
    canonical: "/docs",
  },
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}


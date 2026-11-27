import type { Metadata } from "next";
import React from "react";
import "./globals.css";
import { FAQ_ITEMS } from "@/lib/constants";

const SITE_URL = "https://valkyrie.dev";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
  title: {
    default: "Valkyrie | Terminal-Native AI Coding Agent (BYOK)",
    template: "%s | Valkyrie",
  },
  description:
    "Valkyrie is a terminal-first AI coding agent that plans, edits files, searches the web with DuckDuckGo, and indexes codebases in Pinecone using your own Groq, Gemini, and NVIDIA API keys under explicit approval.",
  keywords: [
    "Valkyrie CLI",
    "terminal AI agent",
    "AI coding CLI",
    "BYOK AI agent",
    "Groq CLI",
    "Gemini CLI",
    "NVIDIA NIM CLI",
    "Pinecone RAG CLI",
    "AES-256-GCM API key vault",
    "local AI developer tool",
  ],
  authors: [{ name: "Valkyrie" }],
  creator: "Valkyrie",
  publisher: "Valkyrie",
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-snippet": -1,
      "max-image-preview": "large",
      "max-video-preview": -1,
    },
  },
  openGraph: {
    title: "Valkyrie | Terminal-Native AI Coding Agent",
    description:
      "Plan, build, and ship from your terminal with Groq, Gemini, and NVIDIA on your own keys. Cloud RAG with Pinecone and approval-gated file edits.",
    url: SITE_URL,
    siteName: "Valkyrie",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Valkyrie | Terminal-Native AI Coding Agent",
    description:
      "Plan, build, and ship from your terminal with Groq, Gemini, and NVIDIA on your own keys.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const softwareJsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "Valkyrie",
    alternateName: "vk",
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Linux, macOS, Windows",
    softwareVersion: "0.1.0",
    url: SITE_URL,
    description:
      "Terminal-native AI coding agent that plans, edits local files with approval gates, searches the web via DuckDuckGo, and indexes codebases in Pinecone using user-supplied Groq, Gemini, and NVIDIA API keys.",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    featureList: [
      "Multi-provider streaming for Groq, Google Gemini, and NVIDIA",
      "Client-side Argon2id + AES-256-GCM API key encryption with Firebase sync",
      "Pinecone cloud RAG codebase indexing and retrieval",
      "Approval-gated local file CRUD and protected path safeguards",
      "SQLite session persistence with /new, /session, /compact, and /model",
    ],
  };

  const websiteJsonLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "Valkyrie",
    url: SITE_URL,
    potentialAction: {
      "@type": "SearchAction",
      target: `${SITE_URL}/docs?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_ITEMS.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.a,
      },
    })),
  };

  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Audiowide&family=Bitcount+Prop+Single:wght@100..900&family=Bitcount+Single:wght@100..900&family=Bruno+Ace+SC&family=Caveat+Brush&family=Comforter+Brush&family=Delius&family=Dongle&family=Funnel+Display:wght@300..800&family=Meddon&family=Monoton&family=Montserrat:ital,wght@0,100..900;1,100..900&family=Mozilla+Headline:wght@200..700&family=Story+Script&family=Varela+Round&family=Zalando+Sans+Expanded:ital,wght@0,200..900;1,200..900&family=Zen+Dots&display=swap"
          rel="stylesheet"
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
        />
      </head>
      <body
        suppressHydrationWarning
        className="antialiased selection:bg-[#FFC929] selection:text-[#1C1D20]"
      >
        {children}
      </body>
    </html>
  );
}

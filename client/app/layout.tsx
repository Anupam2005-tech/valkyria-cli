import type { Metadata } from "next";
import { Instrument_Serif, JetBrains_Mono, Montserrat } from "next/font/google";
import React from "react";
import "./globals.css";

const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-montserrat",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono-google",
  display: "swap",
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["italic"],
  variable: "--font-serif-google",
  display: "swap",
});

const SITE_URL = "https://valkyrie-cli.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
  title: {
    default: "Valkyria | Terminal-Native AI Coding Agent (BYOK)",
    template: "%s | Valkyria",
  },
  description:
    "Valkyria is a terminal-first AI coding agent that plans, edits files, searches the web with DuckDuckGo, and indexes codebases in Pinecone using your own Groq, Gemini, and NVIDIA API keys under explicit approval.",
  keywords: [
    "Valkyria CLI",
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
  authors: [{ name: "Valkyria" }],
  creator: "Valkyria",
  publisher: "Valkyria",
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
    title: "Valkyria | Terminal-Native AI Coding Agent",
    description:
      "Plan, build, and ship from your terminal with Groq, Gemini, and NVIDIA on your own keys. Cloud RAG with Pinecone and approval-gated file edits.",
    url: SITE_URL,
    siteName: "Valkyria",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Valkyria | Terminal-Native AI Coding Agent",
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
    name: "Valkyria",
    alternateName: "vk",
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Linux, macOS, Windows",
    softwareVersion: "0.1.3",
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
      "Local JSON session persistence with /new, /session, /compact, and /model",
    ],
  };

  const websiteJsonLd = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "Valkyria",
    url: SITE_URL,
    potentialAction: {
      "@type": "SearchAction",
      target: `${SITE_URL}/docs?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };

  return (
    <html
      lang="en"
      className={`dark ${montserrat.variable} ${jetbrainsMono.variable} ${instrumentSerif.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
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

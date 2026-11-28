"use client";

import React from "react";

export function BrandLogo({
  name,
  className = "h-5 w-5",
}: {
  name: string;
  className?: string;
}) {
  switch (name.toLowerCase()) {
    case "groq":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="8.5" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="M12 7.5a4.5 4.5 0 1 0 4.5 4.5H12"
            stroke="#FFC929"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "google gemini":
    case "gemini":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <path
            d="M12 2.5c.8 5.2 4.3 8.7 9.5 9.5-5.2.8-8.7 4.3-9.5 9.5-.8-5.2-4.3-8.7-9.5-9.5 5.2-.8 8.7-4.3 9.5-9.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "nvidia nim":
    case "nvidia":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <path
            d="M3.5 12.5c2.2-3.8 5.5-5.5 9-5.5 3.3 0 6.1 1.7 8 5-1.9 3.3-4.7 5-8 5-2.3 0-4.4-.9-6.2-2.6"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
          />
          <circle cx="12.5" cy="12" r="2.3" stroke="#FFC929" strokeWidth="1.6" />
        </svg>
      );
    case "pinecone":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <path
            d="M12 3l6.5 5.2L16 18.5H8L5.5 8.2 12 3Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path
            d="M12 3v15.5M6.8 10.5h10.4M7.7 14.5h8.6"
            stroke="currentColor"
            strokeWidth="1.3"
            opacity="0.7"
          />
        </svg>
      );
    case "firebase":
    case "firebase auth":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <path
            d="M5.5 17.5 8.2 4.5l4.1 6.2 2.9-3.6L18.5 17.5 12 21l-6.5-3.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "langchain":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <path
            d="M9.5 14.5 7 17a3 3 0 0 1-4.2-4.2l2.5-2.5a3 3 0 0 1 4.2 0M14.5 9.5 17 7a3 3 0 0 1 4.2 4.2l-2.5 2.5a3 3 0 0 1-4.2 0"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
          />
          <path
            d="M9.5 14.5 14.5 9.5"
            stroke="#FFC929"
            strokeWidth="1.7"
            strokeLinecap="round"
          />
        </svg>
      );
    case "duckduckgo":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <circle cx="11" cy="11" r="6.5" stroke="currentColor" strokeWidth="1.7" />
          <path
            d="m16 16 4.5 4.5"
            stroke="#FFC929"
            strokeWidth="1.9"
            strokeLinecap="round"
          />
        </svg>
      );
    case "python":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <path
            d="M8.5 7.5V5.8A2.3 2.3 0 0 1 10.8 3.5h2.4a2.3 2.3 0 0 1 2.3 2.3v4.2a2 2 0 0 1-2 2h-3a2 2 0 0 0-2 2v4.2a2.3 2.3 0 0 0 2.3 2.3h2.4a2.3 2.3 0 0 0 2.3-2.3v-1.7"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
          <circle cx="10.5" cy="6" r="0.9" fill="#FFC929" />
          <circle cx="13.5" cy="18" r="0.9" fill="#FFC929" />
        </svg>
      );
    case "next.js":
    case "nextjs":
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
          <path
            d="M8.5 16V8l7.8 10.2M15.5 8v4.8"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
          <polygon
            points="12,3 20,7.5 20,16.5 12,21 4,16.5 4,7.5"
            stroke="currentColor"
            strokeWidth="1.6"
          />
        </svg>
      );
  }
}


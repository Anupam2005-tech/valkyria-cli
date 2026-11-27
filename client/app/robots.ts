import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/docs", "/terms", "/privacy", "/llms.txt"],
      },
    ],
    sitemap: "https://valkyrie.dev/sitemap.xml",
    host: "https://valkyrie.dev",
  };
}

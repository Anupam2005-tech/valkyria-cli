/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  env: {
    // Firebase Web API keys are public identifiers; only this value enters the browser bundle.
    NEXT_PUBLIC_FIREBASE_API_KEY: process.env.FIREBASE_API_KEY ?? "",
  },
};

export default nextConfig;


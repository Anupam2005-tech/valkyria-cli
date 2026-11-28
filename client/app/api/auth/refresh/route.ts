import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const apiKey = process.env.FIREBASE_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "Authentication is not configured." }, { status: 503 });
  }

  let refreshToken: unknown;
  try {
    if (Number(request.headers.get("content-length") || 0) > 16_384) {
      return NextResponse.json({ error: "Invalid request." }, { status: 413 });
    }
    refreshToken = (await request.json()).refreshToken;
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }
  if (typeof refreshToken !== "string" || !refreshToken || refreshToken.length > 8192) {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  try {
    const upstream = await fetch(
      `https://securetoken.googleapis.com/v1/token?key=${encodeURIComponent(apiKey)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: refreshToken }),
        cache: "no-store",
      },
    );
    if (!upstream.ok) {
      return NextResponse.json({ error: "Session refresh failed. Sign in again." }, { status: 401 });
    }
    const data = await upstream.json();
    return NextResponse.json(
      {
        id_token: data.id_token,
        refresh_token: data.refresh_token,
        expires_in: data.expires_in,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return NextResponse.json({ error: "Authentication service unavailable." }, { status: 502 });
  }
}

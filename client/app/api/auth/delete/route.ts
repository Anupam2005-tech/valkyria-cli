import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const apiKey = process.env.FIREBASE_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "Authentication is not configured." }, { status: 503 });
  }

  let idToken: unknown;
  try {
    if (Number(request.headers.get("content-length") || 0) > 16_384) {
      return NextResponse.json({ error: "Invalid request." }, { status: 413 });
    }
    idToken = (await request.json()).idToken;
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }
  if (typeof idToken !== "string" || !idToken || idToken.length > 8192) {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  try {
    const upstream = await fetch(
      `https://identitytoolkit.googleapis.com/v1/accounts:delete?key=${encodeURIComponent(apiKey)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken }),
        cache: "no-store",
      },
    );
    if (upstream.ok) {
      return NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
    }
    const detail = await upstream.json().catch(() => ({}));
    const code = detail?.error?.message === "CREDENTIAL_TOO_OLD_LOGIN_REQUIRED"
      ? "CREDENTIAL_TOO_OLD_LOGIN_REQUIRED"
      : "DELETE_FAILED";
    return NextResponse.json({ error: code }, { status: upstream.status === 400 ? 400 : 502 });
  } catch {
    return NextResponse.json({ error: "Authentication service unavailable." }, { status: 502 });
  }
}

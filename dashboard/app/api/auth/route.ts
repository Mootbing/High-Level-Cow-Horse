import { NextResponse } from "next/server";

const PASSWORD = process.env.DASH_PASSWORD || "REDACTED_PASSWORD";

export async function POST(request: Request) {
  const { password } = await request.json();

  if (password === PASSWORD) {
    const res = NextResponse.json({ ok: true });
    res.cookies.set("dash_auth", "authenticated", {
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 30, // 30 days
      path: "/",
    });
    return res;
  }

  return NextResponse.json({ ok: false, error: "Wrong password" }, { status: 401 });
}

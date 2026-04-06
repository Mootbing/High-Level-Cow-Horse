import { NextRequest, NextResponse } from "next/server";
import { sql } from "@/lib/db";

const ALLOWED_ORIGINS = [
  "https://clarmi.com",
  "https://www.clarmi.com",
  "http://localhost:3000",
];

const RATE_LIMIT_MAX_PER_EMAIL = 3;
const RATE_LIMIT_MAX_PER_IP = 10;

const EMAIL_RE = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

function corsHeaders(origin: string | null) {
  const allowed = origin && ALLOWED_ORIGINS.includes(origin) ? origin : "";
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function getClientIp(req: NextRequest): string {
  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0].trim();
  return req.headers.get("x-real-ip") ?? "unknown";
}

function normalizeUrl(raw: string): string | null {
  let v = raw.trim();
  if (!v) return null;
  if (!v.startsWith("http://") && !v.startsWith("https://")) {
    v = "https://" + v;
  }
  try {
    const parsed = new URL(v);
    if (!parsed.hostname.includes(".")) return null;
    return v;
  } catch {
    return null;
  }
}

export async function OPTIONS(req: NextRequest) {
  const origin = req.headers.get("origin");
  return new NextResponse(null, { status: 204, headers: corsHeaders(origin) });
}

export async function POST(req: NextRequest) {
  const origin = req.headers.get("origin");
  const cors = corsHeaders(origin);

  // Block disallowed origins
  if (origin && !ALLOWED_ORIGINS.includes(origin)) {
    return NextResponse.json(
      { detail: "Forbidden" },
      { status: 403, headers: cors }
    );
  }

  // Parse body
  let body: { url?: string; email?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { detail: "Invalid JSON" },
      { status: 400, headers: cors }
    );
  }

  // Validate URL
  const url = normalizeUrl(body.url ?? "");
  if (!url) {
    return NextResponse.json(
      { detail: "Invalid URL" },
      { status: 400, headers: cors }
    );
  }

  // Validate email
  const email = (body.email ?? "").trim().toLowerCase();
  if (!EMAIL_RE.test(email)) {
    return NextResponse.json(
      { detail: "Invalid email address" },
      { status: 400, headers: cors }
    );
  }

  const clientIp = getClientIp(req);

  // Rate limit via DB — count recent tasks by email and IP
  try {
    const rateLimitRows = await sql`
      SELECT
        COUNT(*) FILTER (WHERE input_data->>'email' = ${email}) AS email_count,
        COUNT(*) FILTER (WHERE input_data->>'client_ip' = ${clientIp}) AS ip_count
      FROM tasks
      WHERE agent_type = 'website_audit'
        AND created_at > NOW() - INTERVAL '1 hour'
        AND (input_data->>'email' = ${email} OR input_data->>'client_ip' = ${clientIp})
    `;

    const { email_count, ip_count } = rateLimitRows[0];
    if (Number(email_count) >= RATE_LIMIT_MAX_PER_EMAIL) {
      return NextResponse.json(
        { detail: "Too many requests for this email. Try again later." },
        { status: 429, headers: cors }
      );
    }
    if (Number(ip_count) >= RATE_LIMIT_MAX_PER_IP) {
      return NextResponse.json(
        { detail: "Too many requests. Try again later." },
        { status: 429, headers: cors }
      );
    }
  } catch (err) {
    console.error("Rate limit check failed:", err);
    // Fail open — don't block the user if the rate limit query fails
  }

  // Insert task
  try {
    const inputData = JSON.stringify({ url, email, client_ip: clientIp });
    const rows = await sql`
      INSERT INTO tasks (id, agent_type, title, input_data, status, priority, retry_count, max_retries, created_at, updated_at)
      VALUES (
        gen_random_uuid(),
        'website_audit',
        ${"Website audit for " + url},
        ${inputData}::jsonb,
        'pending',
        3,
        0,
        3,
        NOW(),
        NOW()
      )
      RETURNING id
    `;

    return NextResponse.json(
      {
        task_id: rows[0].id,
        message: "Your audit is being processed. Check your email shortly!",
      },
      { status: 202, headers: cors }
    );
  } catch (err) {
    console.error("Task insert failed:", err);
    return NextResponse.json(
      { detail: "Something went wrong. Please try again." },
      { status: 500, headers: cors }
    );
  }
}

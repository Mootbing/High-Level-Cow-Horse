"use client";

import { use } from "react";
import Link from "next/link";
import { useProspect } from "@/lib/hooks/use-api";
import { formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  ExternalLink,
  Globe,
  AlertTriangle,
  Palette,
  Type,
  Code,
} from "lucide-react";

export default function ProspectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: prospect, isLoading } = useProspect(id);

  if (isLoading || !prospect) {
    return (
      <div className="space-y-4 animate-in">
        <div className="skeleton h-8 w-48" />
        <div className="card-static">
          <div className="skeleton h-6 w-64 mb-4" />
          <div className="skeleton h-4 w-full mb-2" />
          <div className="skeleton h-4 w-3/4" />
        </div>
      </div>
    );
  }

  const problems = (prospect.raw_data?.site_problems as string[]) || [];

  return (
    <div className="space-y-5 animate-in max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link
          href="/prospects"
          className="p-2 rounded-full hover:bg-[var(--bg-alt)] transition-colors"
        >
          <ArrowLeft size={18} style={{ color: "var(--text-muted)" }} />
        </Link>
        <div>
          <h2
            className="text-2xl tracking-tight"
            style={{ fontFamily: "var(--font-serif)", color: "var(--text)", letterSpacing: "-0.02em" }}
          >
            {prospect.company_name || "Unknown Company"}
          </h2>
          <a
            href={prospect.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-[var(--accent)] hover:underline"
          >
            {prospect.url} <ExternalLink size={10} />
          </a>
        </div>
      </div>

      {/* Info grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Brand Identity */}
        <div className="card-static space-y-4">
          <h3 className="text-label flex items-center gap-2">
            <Palette size={13} style={{ color: "var(--accent)" }} /> Brand Identity
          </h3>

          {prospect.tagline && (
            <p className="text-sm italic" style={{ color: "var(--text-muted)", fontFamily: "var(--font-serif)" }}>
              &ldquo;{prospect.tagline}&rdquo;
            </p>
          )}

          {prospect.brand_colors.length > 0 && (
            <div>
              <span className="text-xs font-medium" style={{ color: "var(--text-light)" }}>Colors</span>
              <div className="flex gap-2.5 mt-1.5">
                {prospect.brand_colors.map((c, i) => (
                  <div key={i} className="flex flex-col items-center gap-1">
                    <span
                      className="w-9 h-9 rounded-[10px] border"
                      style={{ backgroundColor: c, borderColor: "var(--border)" }}
                    />
                    <span className="text-[10px] font-data" style={{ color: "var(--text-light)" }}>
                      {c}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {prospect.fonts.length > 0 && (
            <div>
              <span className="text-xs font-medium flex items-center gap-1" style={{ color: "var(--text-light)" }}>
                <Type size={12} /> Fonts
              </span>
              <div className="flex gap-2 mt-1.5 flex-wrap">
                {prospect.fonts.map((f, i) => (
                  <span
                    key={i}
                    className="text-xs px-2.5 py-1 rounded-full"
                    style={{ backgroundColor: "var(--bg-alt)", color: "var(--text-muted)" }}
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {prospect.industry && (
            <div>
              <span className="text-xs font-medium" style={{ color: "var(--text-light)" }}>Industry</span>
              <p className="text-sm mt-0.5" style={{ color: "var(--text)" }}>{prospect.industry}</p>
            </div>
          )}
        </div>

        {/* Tech & Contact */}
        <div className="card-static space-y-4">
          <h3 className="text-label flex items-center gap-2">
            <Code size={13} style={{ color: "var(--accent)" }} /> Tech & Contact
          </h3>

          {prospect.tech_stack.length > 0 && (
            <div>
              <span className="text-xs font-medium" style={{ color: "var(--text-light)" }}>Tech Stack</span>
              <div className="flex gap-1.5 mt-1.5 flex-wrap">
                {prospect.tech_stack.map((t, i) => (
                  <span
                    key={i}
                    className="text-xs px-2.5 py-1 rounded-full font-data"
                    style={{ backgroundColor: "var(--accent-soft)", color: "var(--accent)" }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {prospect.contact_emails.length > 0 && (
            <div>
              <span className="text-xs font-medium" style={{ color: "var(--text-light)" }}>Emails</span>
              <div className="space-y-0.5 mt-1">
                {prospect.contact_emails.map((e, i) => (
                  <p key={i} className="text-sm font-data" style={{ color: "var(--text)" }}>{e}</p>
                ))}
              </div>
            </div>
          )}

          {Object.keys(prospect.social_links).length > 0 && (
            <div>
              <span className="text-xs font-medium" style={{ color: "var(--text-light)" }}>Social Links</span>
              <div className="space-y-1 mt-1">
                {Object.entries(prospect.social_links).map(([platform, url]) => (
                  <a
                    key={platform}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-[var(--accent)] hover:underline"
                  >
                    <Globe size={12} />
                    {platform}
                    <ExternalLink size={9} />
                  </a>
                ))}
              </div>
            </div>
          )}

          <div>
            <span className="text-xs font-medium" style={{ color: "var(--text-light)" }}>Scraped</span>
            <p className="text-sm font-data mt-0.5" style={{ color: "var(--text-muted)" }}>
              {formatDate(prospect.scraped_at)}
            </p>
          </div>
        </div>
      </div>

      {/* Site Problems */}
      {problems.length > 0 && (
        <div className="card-static">
          <h3 className="text-label flex items-center gap-2 mb-4">
            <AlertTriangle size={13} style={{ color: "var(--status-qa)" }} />
            Site Problems ({problems.length})
          </h3>
          <ul className="space-y-2.5">
            {problems.map((problem, i) => (
              <li
                key={i}
                className="flex items-start gap-2.5 text-sm"
                style={{ color: "var(--text-muted)" }}
              >
                <span
                  className="mt-2 w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: "var(--status-qa)" }}
                />
                {problem}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

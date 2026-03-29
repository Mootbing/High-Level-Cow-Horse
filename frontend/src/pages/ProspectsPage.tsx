import { useEffect, useState } from "react";
import { api } from "../api/client";
import { parseUTC } from "@/lib/utils";
import type { ProspectSummary } from "../types";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";

/** Extract protocol + hostname from a URL to use as grouping key */
function getBaseDomain(url: string): string {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.origin; // e.g. "https://example.com"
  } catch {
    return url;
  }
}

/** Get the pathname portion, or "/" */
function getPath(url: string): string {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.pathname === "/" ? "/" : u.pathname;
  } catch {
    return "/";
  }
}

interface SiteGroup {
  baseDomain: string;
  /** The "main" prospect — shortest path, typically the root "/" */
  main: ProspectSummary;
  /** All other prospects under the same domain */
  subpages: ProspectSummary[];
}

function groupByDomain(prospects: ProspectSummary[]): SiteGroup[] {
  const map = new Map<string, ProspectSummary[]>();

  for (const p of prospects) {
    const base = getBaseDomain(p.url);
    if (!map.has(base)) map.set(base, []);
    map.get(base)!.push(p);
  }

  const groups: SiteGroup[] = [];
  for (const [baseDomain, items] of map) {
    // Sort so shortest path (root) comes first
    items.sort((a, b) => getPath(a.url).length - getPath(b.url).length);
    const [main, ...subpages] = items;
    groups.push({ baseDomain, main, subpages });
  }

  return groups;
}

function ProspectDetails({ p }: { p: ProspectSummary }) {
  return (
    <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
      {p.contact_emails.length > 0 && (
        <span>Emails: {p.contact_emails.join(", ")}</span>
      )}
      {p.brand_colors.length > 0 && (
        <span className="flex items-center gap-1">
          Colors:{" "}
          {p.brand_colors.map((c, i) => (
            <span
              key={i}
              className="inline-block w-4 h-4 rounded border border-border"
              style={{ backgroundColor: c }}
            />
          ))}
        </span>
      )}
      {p.tech_stack.length > 0 && (
        <span>Tech: {p.tech_stack.join(", ")}</span>
      )}
    </div>
  );
}

function SiteCard({ group }: { group: SiteGroup }) {
  const [expanded, setExpanded] = useState(false);
  const { main, subpages, baseDomain } = group;

  // Merge all unique emails, colors, tech from the group for the header
  const allEmails = [...new Set([main, ...subpages].flatMap((p) => p.contact_emails))];
  const allColors = [...new Set([main, ...subpages].flatMap((p) => p.brand_colors))];
  const allTech = [...new Set([main, ...subpages].flatMap((p) => p.tech_stack))];

  return (
    <Card className="overflow-hidden">
      {/* Main site header — always visible */}
      <div
        className="p-5 cursor-pointer hover:bg-accent/30 transition-colors"
        onClick={() => subpages.length > 0 && setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {subpages.length > 0 && (
              expanded ? (
                <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
              )
            )}
            <span className="font-medium text-foreground">
              {main.company_name || "Unknown"}
            </span>
            <a
              href={baseDomain}
              target="_blank"
              rel="noreferrer"
              className="text-foreground/50 hover:text-foreground hover:underline text-sm flex items-center gap-1"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="w-3 h-3" />
              {baseDomain.replace(/^https?:\/\//, "")}
            </a>
            {subpages.length > 0 && (
              <span className="text-xs text-muted-foreground">
                ({subpages.length + 1} pages)
              </span>
            )}
          </div>
          {main.industry && (
            <Badge variant="secondary">{main.industry}</Badge>
          )}
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          {allEmails.length > 0 && (
            <span>Emails: {allEmails.join(", ")}</span>
          )}
          {allColors.length > 0 && (
            <span className="flex items-center gap-1">
              Colors:{" "}
              {allColors.map((c, i) => (
                <span
                  key={i}
                  className="inline-block w-4 h-4 rounded border border-border"
                  style={{ backgroundColor: c }}
                />
              ))}
            </span>
          )}
          {allTech.length > 0 && (
            <span>Tech: {allTech.join(", ")}</span>
          )}
        </div>
      </div>

      {/* Collapsible subpages */}
      {expanded && subpages.length > 0 && (
        <div className="border-t border-border">
          {/* Show root page first */}
          <div className="px-5 py-3 bg-accent/10 border-b border-border/50">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium text-foreground/80">/</span>
              <span className="text-xs text-muted-foreground">root</span>
            </div>
            <ProspectDetails p={main} />
          </div>
          {/* Then subpages */}
          {subpages.map((sp) => (
            <div
              key={sp.id}
              className="px-5 py-3 bg-accent/10 border-b border-border/50 last:border-b-0"
            >
              <div className="flex items-center gap-2 mb-1">
                <a
                  href={sp.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-foreground/80 hover:text-foreground hover:underline"
                >
                  {getPath(sp.url)}
                </a>
                {sp.scraped_at && (
                  <span className="text-xs text-muted-foreground">
                    {parseUTC(sp.scraped_at)?.toLocaleDateString()}
                  </span>
                )}
              </div>
              <ProspectDetails p={sp} />
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<ProspectSummary[]>([]);

  useEffect(() => {
    api.prospects().then(setProspects).catch(() => {});
  }, []);

  const groups = groupByDomain(prospects);

  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-6 text-foreground">Prospects</h2>

      {groups.length === 0 ? (
        <p className="text-muted-foreground">
          No prospects scraped yet. Use Chat to scrape a website.
        </p>
      ) : (
        <div className="space-y-3">
          {groups.map((g) => (
            <SiteCard key={g.baseDomain} group={g} />
          ))}
        </div>
      )}
    </div>
  );
}

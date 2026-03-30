import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ProspectSummary } from "../types";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { ExternalLink } from "lucide-react";

const SEED_PROSPECTS: ProspectSummary[] = [
  {
    id: "seed-rosniyom",
    url: "https://www.rosniyomnyc.com",
    company_name: "Ros Niyom Thai Restaurant",
    industry: "Restaurant / Thai Cuisine",
    contact_emails: [],
    brand_colors: [],
    tech_stack: ["Wix", "Wix Media", "Online Ordering System"],
    scraped_at: new Date().toISOString(),
  },
];

/** Extract protocol + hostname from a URL to use as grouping key */
function getBaseDomain(url: string): string {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.origin;
  } catch {
    return url;
  }
}

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
  main: ProspectSummary;
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
    items.sort((a, b) => getPath(a.url).length - getPath(b.url).length);
    const [main, ...subpages] = items;
    groups.push({ baseDomain, main, subpages });
  }

  return groups;
}

const PLACEHOLDER_GRADIENTS = [
  "from-violet-600 to-indigo-600",
  "from-cyan-600 to-blue-600",
  "from-emerald-600 to-teal-600",
  "from-orange-600 to-rose-600",
  "from-fuchsia-600 to-pink-600",
  "from-sky-600 to-cyan-600",
];

function hashIndex(str: string, max: number) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return Math.abs(h) % max;
}

function WebsiteThumbnail({ url, name }: { url: string; name: string }) {
  const [imgError, setImgError] = useState(false);
  const gradient =
    PLACEHOLDER_GRADIENTS[hashIndex(name, PLACEHOLDER_GRADIENTS.length)];

  if (imgError) {
    return (
      <div
        className={`w-full h-40 rounded-t-lg bg-gradient-to-br ${gradient} flex items-center justify-center`}
      >
        <span className="text-white/80 text-3xl font-bold uppercase tracking-wider">
          {name.slice(0, 2)}
        </span>
      </div>
    );
  }

  const thumbUrl = `https://image.thum.io/get/width/600/crop/400/${url}`;

  return (
    <div className="w-full h-40 rounded-t-lg overflow-hidden bg-muted">
      <img
        src={thumbUrl}
        alt={`${name} preview`}
        className="w-full h-full object-cover object-top"
        loading="lazy"
        onError={() => setImgError(true)}
      />
    </div>
  );
}

function SiteCard({ group }: { group: SiteGroup }) {
  const { main, subpages, baseDomain } = group;
  const allEmails = [
    ...new Set([main, ...subpages].flatMap((p) => p.contact_emails)),
  ];
  const allColors = [
    ...new Set([main, ...subpages].flatMap((p) => p.brand_colors)),
  ];
  const allTech = [
    ...new Set([main, ...subpages].flatMap((p) => p.tech_stack)),
  ];
  const displayName = main.company_name || baseDomain.replace(/^https?:\/\//, "");

  return (
    <Card className="overflow-hidden hover:bg-accent/50 transition-colors group">
      <WebsiteThumbnail url={baseDomain} name={displayName} />
      <div className="p-4">
        <div className="flex items-center justify-between mb-1">
          <span className="font-medium text-foreground truncate block">
            {displayName}
          </span>
          {main.industry && (
            <Badge variant="secondary">{main.industry}</Badge>
          )}
        </div>

        <a
          href={baseDomain}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-foreground/60 hover:text-foreground hover:underline flex items-center gap-1 mb-2"
        >
          <ExternalLink className="w-3 h-3" />
          {baseDomain.replace(/^https?:\/\//, "")}
        </a>

        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
          {allColors.length > 0 && (
            <span className="flex items-center gap-1">
              Colors:
              {allColors.map((c, i) => (
                <span
                  key={i}
                  className="inline-block w-3.5 h-3.5 rounded border border-border"
                  style={{ backgroundColor: c }}
                />
              ))}
            </span>
          )}
          {allTech.length > 0 && (
            <span className="truncate max-w-[200px]">
              Tech: {allTech.join(", ")}
            </span>
          )}
          {allEmails.length > 0 && (
            <span className="truncate max-w-[200px]">
              {allEmails.join(", ")}
            </span>
          )}
          {subpages.length > 0 && (
            <span>{subpages.length + 1} pages scraped</span>
          )}
        </div>
      </div>
    </Card>
  );
}

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<ProspectSummary[]>([]);

  useEffect(() => {
    api
      .prospects()
      .then((data) => setProspects(data.length ? data : SEED_PROSPECTS))
      .catch(() => setProspects(SEED_PROSPECTS));
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {groups.map((g) => (
            <SiteCard key={g.baseDomain} group={g} />
          ))}
        </div>
      )}
    </div>
  );
}

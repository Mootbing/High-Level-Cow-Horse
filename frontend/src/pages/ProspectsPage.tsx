import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ProspectSummary } from "../types";

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<ProspectSummary[]>([]);

  useEffect(() => {
    api.prospects().then(setProspects).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-6">Prospects</h2>

      {prospects.length === 0 ? (
        <p className="text-white/40">No prospects scraped yet. Use Chat to scrape a website.</p>
      ) : (
        <div className="space-y-3">
          {prospects.map((p) => (
            <div
              key={p.id}
              className="bg-white/5 border border-white/5 rounded-lg p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="font-medium">
                    {p.company_name || "Unknown"}
                  </span>
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-500 hover:underline text-sm ml-3"
                  >
                    {p.url}
                  </a>
                </div>
                {p.industry && (
                  <span className="text-xs bg-white/10 px-2 py-0.5 rounded text-white/60">
                    {p.industry}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-4 text-sm text-white/50">
                {p.contact_emails.length > 0 && (
                  <span>Emails: {p.contact_emails.join(", ")}</span>
                )}
                {p.brand_colors.length > 0 && (
                  <span className="flex items-center gap-1">
                    Colors:{" "}
                    {p.brand_colors.map((c, i) => (
                      <span
                        key={i}
                        className="inline-block w-4 h-4 rounded border border-white/20"
                        style={{ backgroundColor: c }}
                      />
                    ))}
                  </span>
                )}
                {p.tech_stack.length > 0 && (
                  <span>Tech: {p.tech_stack.join(", ")}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

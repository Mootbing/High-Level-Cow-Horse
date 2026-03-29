import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ProspectSummary } from "../types";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

export default function ProspectsPage() {
  const [prospects, setProspects] = useState<ProspectSummary[]>([]);

  useEffect(() => {
    api.prospects().then(setProspects).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-6 text-foreground">Prospects</h2>

      {prospects.length === 0 ? (
        <p className="text-muted-foreground">
          No prospects scraped yet. Use Chat to scrape a website.
        </p>
      ) : (
        <div className="space-y-3">
          {prospects.map((p) => (
            <Card key={p.id} className="p-5">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="font-medium text-foreground">
                    {p.company_name || "Unknown"}
                  </span>
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-foreground/50 hover:text-foreground hover:underline text-sm ml-3"
                  >
                    {p.url}
                  </a>
                </div>
                {p.industry && (
                  <Badge variant="secondary">{p.industry}</Badge>
                )}
              </div>
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
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

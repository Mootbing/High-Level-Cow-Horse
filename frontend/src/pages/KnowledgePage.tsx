import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { KnowledgeEntry } from "../types";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Select } from "../components/ui/select";
import { ExternalLink } from "lucide-react";

const CATEGORIES = [
  "",
  "trend",
  "technique",
  "component",
  "tool",
  "inspiration",
  "code_pattern",
  "design_rule",
  "learning",
];

export default function KnowledgePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [category, setCategory] = useState("");

  useEffect(() => {
    api.knowledge(category || undefined).then(setEntries).catch(() => {});
  }, [category]);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-foreground">Knowledge Base</h2>
        <Select value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c || "All categories"}
            </option>
          ))}
        </Select>
      </div>

      {entries.length === 0 ? (
        <p className="text-muted-foreground">
          No knowledge entries yet. The Research agent adds these automatically.
        </p>
      ) : (
        <div className="space-y-3">
          {entries.map((k) => (
            <Card key={k.id} className="p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-foreground">{k.title}</h3>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{k.category}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {(k.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-3">
                {k.content}
              </p>
              {k.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {k.tags.map((tag, i) => (
                    <Badge
                      key={i}
                      variant="outline"
                      className="text-xs text-muted-foreground"
                    >
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
              {k.source_url && (
                <a
                  href={k.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-2 hover:underline"
                >
                  <ExternalLink className="w-3 h-3" />
                  Source
                </a>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

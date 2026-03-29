import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { KnowledgeEntry } from "../types";

const CATEGORIES = ["", "trend", "technique", "component", "tool", "inspiration", "code_pattern", "design_rule", "learning"];

export default function KnowledgePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [category, setCategory] = useState("");

  useEffect(() => {
    api.knowledge(category || undefined).then(setEntries).catch(() => {});
  }, [category]);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold">Knowledge Base</h2>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c || "All categories"}
            </option>
          ))}
        </select>
      </div>

      {entries.length === 0 ? (
        <p className="text-white/40">No knowledge entries yet. The Research agent adds these automatically.</p>
      ) : (
        <div className="space-y-3">
          {entries.map((k) => (
            <div
              key={k.id}
              className="bg-white/5 border border-white/5 rounded-lg p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{k.title}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-white/10 px-2 py-0.5 rounded text-white/60">
                    {k.category}
                  </span>
                  <span className="text-xs text-white/30">
                    {(k.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <p className="text-sm text-white/50 line-clamp-3">{k.content}</p>
              {k.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {k.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="text-xs bg-brand-600/20 text-brand-500 px-2 py-0.5 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              {k.source_url && (
                <a
                  href={k.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-brand-500 hover:underline mt-2 inline-block"
                >
                  Source &rarr;
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

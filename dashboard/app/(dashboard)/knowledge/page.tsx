"use client";

import { useState } from "react";
import { useKnowledge } from "@/lib/hooks/use-api";
import { formatDate } from "@/lib/utils";
import { Search, BookOpen, Tag, ExternalLink } from "lucide-react";

const CATEGORIES = ["all", "design_trend", "animation_technique", "code_pattern", "tool", "lesson_learned"] as const;

const CATEGORY_LABELS: Record<string, string> = {
  design_trend: "Design Trend",
  animation_technique: "Animation",
  code_pattern: "Code Pattern",
  tool: "Tool",
  lesson_learned: "Lesson",
};

export default function KnowledgePage() {
  const [category, setCategory] = useState<string | undefined>();
  const [search, setSearch] = useState("");

  const { data, isLoading } = useKnowledge({
    category,
    search: search || undefined,
    limit: 50,
  });

  return (
    <div className="space-y-4 animate-in">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div
          className="flex items-center gap-2 px-4 py-2.5 rounded-full w-full sm:w-64 border transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_var(--accent-soft)]"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <Search size={14} style={{ color: "var(--text-light)" }} />
          <input
            type="text"
            placeholder="Search knowledge..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none outline-none text-sm flex-1"
            style={{ color: "var(--text)" }}
          />
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c === "all" ? undefined : c)}
              className={`text-xs px-3 py-1.5 rounded-full transition-all duration-300 ${
                (c === "all" && !category) || category === c
                  ? "btn-primary"
                  : "btn-outline"
              }`}
            >
              {c === "all" ? "All" : CATEGORY_LABELS[c] || c}
            </button>
          ))}
        </div>
      </div>

      {/* Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card-static h-40">
              <div className="skeleton h-4 w-32 mb-3" />
              <div className="skeleton h-3 w-full mb-2" />
              <div className="skeleton h-3 w-3/4" />
            </div>
          ))}
        </div>
      ) : data?.items.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((entry) => (
            <div key={entry.id} className="card space-y-2.5">
              <div className="flex items-start justify-between">
                <h4 className="text-sm font-semibold flex items-center gap-1.5 pr-2" style={{ color: "var(--text)" }}>
                  <BookOpen size={13} style={{ color: "var(--accent)" }} />
                  {entry.title}
                </h4>
                <span className="text-[10px] px-2 py-0.5 rounded-full flex-shrink-0" style={{ backgroundColor: "var(--bg-alt)", color: "var(--text-muted)" }}>
                  {CATEGORY_LABELS[entry.category] || entry.category}
                </span>
              </div>

              <p className="text-xs leading-relaxed line-clamp-3" style={{ color: "var(--text-muted)" }}>
                {entry.content}
              </p>

              {entry.tags.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {entry.tags.map((tag, i) => (
                    <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full flex items-center gap-0.5"
                      style={{ backgroundColor: "var(--accent-soft)", color: "var(--accent)" }}>
                      <Tag size={8} />{tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between pt-1">
                {entry.source_url && (
                  <a href={entry.source_url} target="_blank" rel="noopener noreferrer"
                    className="text-[10px] text-[var(--accent)] flex items-center gap-0.5 hover:underline">
                    Source <ExternalLink size={8} />
                  </a>
                )}
                <div className="flex items-center gap-2 ml-auto">
                  <span className="text-[10px] font-data" style={{ color: "var(--text-light)" }}>
                    {entry.relevance_score.toFixed(2)}
                  </span>
                  <span className="text-[10px]" style={{ color: "var(--text-light)" }}>
                    {formatDate(entry.created_at)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card-static py-16 text-center">
          <BookOpen size={32} className="mx-auto mb-3" style={{ color: "var(--text-light)" }} />
          <p className="text-sm" style={{ color: "var(--text-light)" }}>No knowledge entries yet</p>
        </div>
      )}
    </div>
  );
}

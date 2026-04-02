"use client";

import { useState, useRef, useEffect } from "react";
import { useKnowledge } from "@/lib/hooks/use-api";
import { useSearch } from "@/lib/search-context";
import { ToolbarSlot } from "@/lib/toolbar-context";
import { formatDate } from "@/lib/utils";
import { BookOpen, Tag, ExternalLink, Filter, Check } from "lucide-react";

const CATEGORIES = ["design_trend", "animation_technique", "code_pattern", "tool", "lesson_learned"] as const;

const CATEGORY_LABELS: Record<string, string> = {
  design_trend: "Design Trend",
  animation_technique: "Animation",
  code_pattern: "Code Pattern",
  tool: "Tool",
  lesson_learned: "Lesson",
};

const CATEGORY_COLORS: Record<string, string> = {
  design_trend: "#7C5CFC",
  animation_technique: "#60A5FA",
  code_pattern: "#34C759",
  tool: "#ff9f0a",
  lesson_learned: "#E879A8",
};

export default function KnowledgePage() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);
  const { search } = useSearch();

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setFilterOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const { data, isLoading } = useKnowledge({
    category: selectedCategories.length === 1 ? selectedCategories[0] : undefined,
    search: search || undefined,
    limit: 50,
  });

  // Client-side filter for multi-category
  const filteredItems = selectedCategories.length > 1
    ? data?.items.filter((e) => selectedCategories.includes(e.category))
    : data?.items;

  function toggleCategory(c: string) {
    setSelectedCategories((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  }

  return (
    <div className="space-y-4 animate-in">
      <ToolbarSlot count={filteredItems?.length ?? data?.total ?? 0}>
        <div className="relative" ref={filterRef}>
          <button
            onClick={() => setFilterOpen(!filterOpen)}
            className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-all duration-300 ${
              selectedCategories.length > 0
                ? "border-[var(--accent)] bg-[var(--accent-soft)]"
                : ""
            }`}
            style={{
              borderColor: selectedCategories.length > 0 ? "var(--accent)" : "var(--border)",
              color: "var(--text)",
              backgroundColor: selectedCategories.length > 0 ? "var(--accent-soft)" : "var(--bg-card)",
            }}
          >
            <Filter size={12} />
            Category
            {selectedCategories.length > 0 && (
              <span
                className="flex items-center justify-center rounded-full text-[10px] font-semibold text-white"
                style={{ backgroundColor: "var(--accent)", minWidth: 16, height: 16 }}
              >
                {selectedCategories.length}
              </span>
            )}
          </button>

          {filterOpen && (
            <div
              className="absolute top-full left-0 mt-2 w-52 rounded-xl border shadow-lg z-50 overflow-hidden"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border)",
                boxShadow: "0 12px 40px rgba(0,0,0,0.1)",
              }}
            >
              <div className="p-1.5">
                {CATEGORIES.map((c) => {
                  const active = selectedCategories.includes(c);
                  const color = CATEGORY_COLORS[c] || "var(--accent)";
                  return (
                    <button
                      key={c}
                      onClick={() => toggleCategory(c)}
                      className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-left text-sm transition-colors duration-150 hover:bg-[var(--bg-alt)]"
                      style={{ color: "var(--text)" }}
                    >
                      <span
                        className="flex items-center justify-center w-4 h-4 rounded border transition-all duration-200"
                        style={{
                          borderColor: active ? color : "var(--border)",
                          backgroundColor: active ? color : "transparent",
                        }}
                      >
                        {active && <Check size={10} color="white" strokeWidth={3} />}
                      </span>
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                      <span className="flex-1">{CATEGORY_LABELS[c] || c}</span>
                    </button>
                  );
                })}
              </div>
              {selectedCategories.length > 0 && (
                <div style={{ borderTop: "1px solid var(--border)" }} className="p-1.5">
                  <button
                    onClick={() => setSelectedCategories([])}
                    className="w-full px-3 py-2 rounded-lg text-xs text-left transition-colors duration-150 hover:bg-[var(--bg-alt)]"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Clear filters
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {selectedCategories.map((c) => (
          <button
            key={c}
            onClick={() => toggleCategory(c)}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all duration-200"
            style={{
              backgroundColor: (CATEGORY_COLORS[c] || "var(--accent)") + "18",
              color: CATEGORY_COLORS[c] || "var(--accent)",
              border: `1px solid ${CATEGORY_COLORS[c] || "var(--accent)"}30`,
            }}
          >
            {CATEGORY_LABELS[c] || c}
            <span className="ml-0.5">&times;</span>
          </button>
        ))}
      </ToolbarSlot>

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
      ) : filteredItems?.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((entry) => (
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

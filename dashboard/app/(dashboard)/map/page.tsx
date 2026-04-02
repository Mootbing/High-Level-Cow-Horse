"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import { useProspectsGeo } from "@/lib/hooks/use-api";
import { useSearch } from "@/lib/search-context";
import { ToolbarSlot } from "@/lib/toolbar-context";
import { STATUS_COLORS, STATUS_LABELS } from "@/lib/constants";
import { Filter, Check } from "lucide-react";

const MapView = dynamic(() => import("@/components/map/map-container"), {
  ssr: false,
  loading: () => (
    <div className="w-full skeleton" style={{ height: "calc(100vh - 10rem)", borderRadius: "var(--radius-lg)" }} />
  ),
});

const STATUS_OPTIONS = ["intake", "pitch", "design", "build", "qa", "deployed"] as const;

export default function MapPage() {
  const { data: prospects, isLoading } = useProspectsGeo();
  const { search } = useSearch();
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setFilterOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function toggleStatus(s: string) {
    setSelectedStatuses((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  }

  const filtered = useMemo(() => {
    if (!prospects) return [];
    let items = prospects;
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (p) =>
          (p.company_name?.toLowerCase().includes(q)) ||
          (p.industry?.toLowerCase().includes(q)) ||
          (p.url?.toLowerCase().includes(q))
      );
    }
    if (selectedStatuses.length > 0) {
      items = items.filter((p) => {
        if (!p.project_status) return selectedStatuses.includes("none");
        return selectedStatuses.includes(p.project_status);
      });
    }
    return items;
  }, [prospects, search, selectedStatuses]);

  return (
    <div className="space-y-4 animate-in">
      <ToolbarSlot count={filtered.length}>
        <div className="relative" ref={filterRef}>
          <button
            onClick={() => setFilterOpen(!filterOpen)}
            className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition-all duration-300 ${
              selectedStatuses.length > 0
                ? "border-[var(--accent)] bg-[var(--accent-soft)]"
                : ""
            }`}
            style={{
              borderColor: selectedStatuses.length > 0 ? "var(--accent)" : "var(--border)",
              color: "var(--text)",
              backgroundColor: selectedStatuses.length > 0 ? "var(--accent-soft)" : "var(--bg-card)",
            }}
          >
            <Filter size={12} />
            Status
            {selectedStatuses.length > 0 && (
              <span
                className="flex items-center justify-center rounded-full text-[10px] font-semibold text-white"
                style={{ backgroundColor: "var(--accent)", minWidth: 16, height: 16 }}
              >
                {selectedStatuses.length}
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
                {STATUS_OPTIONS.map((s) => {
                  const active = selectedStatuses.includes(s);
                  const color = STATUS_COLORS[s] || "#8e8e93";
                  return (
                    <button
                      key={s}
                      onClick={() => toggleStatus(s)}
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
                      <span className="flex-1">{STATUS_LABELS[s] || s}</span>
                    </button>
                  );
                })}
                <button
                  onClick={() => toggleStatus("none")}
                  className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-left text-sm transition-colors duration-150 hover:bg-[var(--bg-alt)]"
                  style={{ color: "var(--text)" }}
                >
                  <span
                    className="flex items-center justify-center w-4 h-4 rounded border transition-all duration-200"
                    style={{
                      borderColor: selectedStatuses.includes("none") ? "#8e8e93" : "var(--border)",
                      backgroundColor: selectedStatuses.includes("none") ? "#8e8e93" : "transparent",
                    }}
                  >
                    {selectedStatuses.includes("none") && <Check size={10} color="white" strokeWidth={3} />}
                  </span>
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: "#8e8e93" }} />
                  <span className="flex-1">No project</span>
                </button>
              </div>
              {selectedStatuses.length > 0 && (
                <div style={{ borderTop: "1px solid var(--border)" }} className="p-1.5">
                  <button
                    onClick={() => setSelectedStatuses([])}
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

        {selectedStatuses.map((s) => (
          <button
            key={s}
            onClick={() => toggleStatus(s)}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all duration-200"
            style={{
              backgroundColor: (STATUS_COLORS[s] || "#8e8e93") + "18",
              color: STATUS_COLORS[s] || "#8e8e93",
              border: `1px solid ${STATUS_COLORS[s] || "#8e8e93"}30`,
            }}
          >
            {s === "none" ? "No project" : STATUS_LABELS[s] || s}
            <span className="ml-0.5">&times;</span>
          </button>
        ))}
      </ToolbarSlot>

      <div className="card-static p-0 overflow-hidden" style={{ height: "calc(100vh - 10rem)" }}>
        <MapView prospects={filtered} isLoading={isLoading} />
      </div>
    </div>
  );
}

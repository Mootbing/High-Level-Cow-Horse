"use client";

import { useState, useRef, useEffect } from "react";
import { useEmails } from "@/lib/hooks/use-api";
import { STATUS_COLORS, STATUS_LABELS } from "@/lib/constants";
import { ToolbarSlot } from "@/lib/toolbar-context";
import { EmailTable } from "@/components/tables/email-table";
import { ChevronLeft, ChevronRight, Filter, Check } from "lucide-react";

const EMAIL_STATUSES = ["draft", "pending", "sent", "failed"] as const;

export default function EmailsPage() {
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState("-created_at");
  const limit = 25;

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
    setPage(0);
  }

  const statusParam = selectedStatuses.length > 0 ? selectedStatuses.join(",") : undefined;

  const { data, isLoading } = useEmails({
    offset: page * limit,
    limit,
    status: statusParam,
    sort,
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="space-y-4 animate-in">
      <ToolbarSlot count={data?.total ?? 0}>
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
              className="absolute top-full left-0 mt-2 w-48 rounded-xl border shadow-lg z-50 overflow-hidden"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border)",
                boxShadow: "0 12px 40px rgba(0,0,0,0.1)",
              }}
            >
              <div className="p-1.5">
                {EMAIL_STATUSES.map((s) => {
                  const active = selectedStatuses.includes(s);
                  const color = STATUS_COLORS[s] || "var(--text-muted)";
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
              </div>
              {selectedStatuses.length > 0 && (
                <div style={{ borderTop: "1px solid var(--border)" }} className="p-1.5">
                  <button
                    onClick={() => { setSelectedStatuses([]); setPage(0); }}
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
              backgroundColor: (STATUS_COLORS[s] || "#888") + "18",
              color: STATUS_COLORS[s] || "#888",
              border: `1px solid ${STATUS_COLORS[s] || "#888"}30`,
            }}
          >
            {STATUS_LABELS[s] || s}
            <span className="ml-0.5">&times;</span>
          </button>
        ))}
      </ToolbarSlot>

      {/* Table */}
      <div className="card-static p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton h-10 w-full" />
            ))}
          </div>
        ) : (
          <EmailTable emails={data?.items || []} sort={sort} onSort={setSort} />
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-5 py-3" style={{ borderTop: "1px solid var(--border)" }}>
            <span className="text-xs" style={{ color: "var(--text-light)" }}>Page {page + 1} of {totalPages}</span>
            <div className="flex gap-1">
              <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                className="p-1.5 rounded-full hover:bg-[var(--bg-alt)] disabled:opacity-30 transition-colors">
                <ChevronLeft size={16} />
              </button>
              <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1}
                className="p-1.5 rounded-full hover:bg-[var(--bg-alt)] disabled:opacity-30 transition-colors">
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

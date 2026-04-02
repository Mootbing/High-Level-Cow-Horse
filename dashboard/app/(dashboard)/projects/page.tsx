"use client";

import { useState, useRef, useEffect } from "react";
import { useProjects, useProjectStats } from "@/lib/hooks/use-api";
import { useSearch } from "@/lib/search-context";
import { ToolbarSlot } from "@/lib/toolbar-context";
import { ProjectCard } from "@/components/cards/project-card";
import { StatusBadge } from "@/components/data/status-badge";
import { PIPELINE_STAGES, STATUS_LABELS, STATUS_COLORS } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import { SortableHeader } from "@/components/data/sortable-header";
import Link from "next/link";
import { LayoutGrid, List, ChevronLeft, ChevronRight, ExternalLink, Filter, Check } from "lucide-react";

type View = "kanban" | "table";

export default function ProjectsPage() {
  const [view, setView] = useState<View>("kanban");
  const { search } = useSearch();
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState("-updated_at");
  const limit = 50;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setFilterOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const statusParam = selectedStatuses.length > 0 ? selectedStatuses.join(",") : undefined;

  const { data: stats } = useProjectStats();
  const { data, isLoading } = useProjects({
    offset: page * limit,
    limit,
    search: search || undefined,
    status: statusParam,
    sort,
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  function toggleStatus(s: string) {
    setSelectedStatuses((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
    setPage(0);
  }

  return (
    <div className="space-y-4 animate-in">
      <ToolbarSlot count={data?.total ?? stats?.total ?? 0}>
        {/* Status filter dropdown */}
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
                {PIPELINE_STAGES.map((s) => {
                  const active = selectedStatuses.includes(s);
                  const count = stats?.by_status[s] || 0;
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
                          borderColor: active ? STATUS_COLORS[s] : "var(--border)",
                          backgroundColor: active ? STATUS_COLORS[s] : "transparent",
                        }}
                      >
                        {active && <Check size={10} color="white" strokeWidth={3} />}
                      </span>
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: STATUS_COLORS[s] }}
                      />
                      <span className="flex-1">{STATUS_LABELS[s]}</span>
                      <span className="text-xs font-data" style={{ color: "var(--text-light)" }}>
                        {count}
                      </span>
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

        {/* Active filter badges */}
        {selectedStatuses.length > 0 && (
          <>
            {selectedStatuses.map((s) => (
              <button
                key={s}
                onClick={() => toggleStatus(s)}
                className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all duration-200"
                style={{
                  backgroundColor: STATUS_COLORS[s] + "18",
                  color: STATUS_COLORS[s],
                  border: `1px solid ${STATUS_COLORS[s]}30`,
                }}
              >
                {STATUS_LABELS[s]}
                <span className="ml-0.5">&times;</span>
              </button>
            ))}
          </>
        )}

        {/* View toggle */}
        <div className="flex gap-0.5 p-0.5 rounded-full border" style={{ borderColor: "var(--border)" }}>
          <button
            onClick={() => setView("kanban")}
            className={`p-1.5 rounded-full transition-all duration-300 ${
              view === "kanban" ? "bg-[var(--text)] text-[var(--bg)]" : ""
            }`}
          >
            <LayoutGrid size={13} style={{ color: view === "kanban" ? "var(--bg)" : "var(--text-light)" }} />
          </button>
          <button
            onClick={() => setView("table")}
            className={`p-1.5 rounded-full transition-all duration-300 ${
              view === "table" ? "bg-[var(--text)] text-[var(--bg)]" : ""
            }`}
          >
            <List size={13} style={{ color: view === "table" ? "var(--bg)" : "var(--text-light)" }} />
          </button>
        </div>
      </ToolbarSlot>

      {/* Kanban View */}
      {view === "kanban" && selectedStatuses.length === 0 && (
        <div className="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory">
          {PIPELINE_STAGES.map((stage) => {
            const items = data?.items.filter((p) => p.status === stage) || [];
            return (
              <div key={stage} className="min-w-[290px] w-[290px] flex-shrink-0 snap-start">
                <div className="flex items-center gap-2 mb-3 px-1">
                  <StatusBadge status={stage} />
                  <span className="text-xs font-data" style={{ color: "var(--text-light)" }}>
                    {items.length}
                  </span>
                </div>
                <div className="space-y-3">
                  {items.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                  ))}
                  {items.length === 0 && (
                    <div
                      className="rounded-[var(--radius-lg)] border-2 border-dashed p-8 text-center text-xs"
                      style={{ borderColor: "var(--border)", color: "var(--text-light)" }}
                    >
                      No projects
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Table View */}
      {(view === "table" || selectedStatuses.length > 0) && (
        <div className="card-static p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {[
                    { label: "Name", key: "name" },
                    { label: "Company", key: null },
                    { label: "Status", key: "status" },
                    { label: "Priority", key: "priority" },
                    { label: "Tasks", key: null },
                    { label: "Emails", key: null },
                    { label: "Deployed", key: null },
                    { label: "Updated", key: "updated_at" },
                  ].map((col) => (
                    <SortableHeader key={col.label} label={col.label} sortKey={col.key} currentSort={sort} onSort={setSort} />
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                        {Array.from({ length: 8 }).map((_, j) => (
                          <td key={j} className="px-5 py-3.5"><div className="skeleton h-4 w-20" /></td>
                        ))}
                      </tr>
                    ))
                  : data?.items.map((p) => (
                      <tr
                        key={p.id}
                        className="transition-colors duration-200 hover:bg-[var(--bg-alt)]"
                        style={{ borderBottom: "1px solid var(--border)" }}
                      >
                        <td className="px-5 py-3.5">
                          <Link href={`/projects/${p.id}`} className="font-medium hover:text-[var(--accent)] transition-colors" style={{ color: "var(--text)" }}>
                            {p.name}
                          </Link>
                        </td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-muted)" }}>{p.prospect_company || "—"}</td>
                        <td className="px-5 py-3.5"><StatusBadge status={p.status} /></td>
                        <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>{p.priority}</td>
                        <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>{p.task_count}</td>
                        <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>{p.email_count}</td>
                        <td className="px-5 py-3.5">
                          {p.deployed_url ? (
                            <a href={p.deployed_url} target="_blank" rel="noopener noreferrer"
                              className="flex items-center gap-1 text-xs text-[var(--status-deployed)] hover:underline">
                              Live <ExternalLink size={10} />
                            </a>
                          ) : <span className="text-xs" style={{ color: "var(--text-light)" }}>—</span>}
                        </td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(p.updated_at)}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>

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
      )}
    </div>
  );
}

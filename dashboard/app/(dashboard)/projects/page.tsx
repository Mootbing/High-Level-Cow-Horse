"use client";

import { useState } from "react";
import { useProjects, useProjectStats } from "@/lib/hooks/use-api";
import { ProjectCard } from "@/components/cards/project-card";
import { StatusBadge } from "@/components/data/status-badge";
import { PIPELINE_STAGES, STATUS_LABELS } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import { Search, LayoutGrid, List, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";

type View = "kanban" | "table";

export default function ProjectsPage() {
  const [view, setView] = useState<View>("kanban");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(0);
  const limit = 50;

  const { data: stats } = useProjectStats();
  const { data, isLoading } = useProjects({
    offset: page * limit,
    limit,
    search: search || undefined,
    status: statusFilter,
    sort: "-updated_at",
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

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
            placeholder="Search projects..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            className="bg-transparent border-none outline-none text-sm flex-1"
            style={{ color: "var(--text)" }}
          />
        </div>

        {/* Status filter pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setStatusFilter(undefined)}
            className={`text-xs px-3 py-1.5 rounded-full transition-all duration-300 ${
              !statusFilter ? "btn-primary" : "btn-outline"
            }`}
          >
            All ({stats?.total || 0})
          </button>
          {PIPELINE_STAGES.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s === statusFilter ? undefined : s)}
              className={`text-xs px-3 py-1.5 rounded-full transition-all duration-300 ${
                statusFilter === s ? "btn-primary" : "btn-outline"
              }`}
            >
              {STATUS_LABELS[s]} ({stats?.by_status[s] || 0})
            </button>
          ))}
        </div>

        {/* View toggle */}
        <div className="ml-auto flex gap-0.5 p-1 rounded-full border" style={{ borderColor: "var(--border)" }}>
          <button
            onClick={() => setView("kanban")}
            className={`p-1.5 rounded-full transition-all duration-300 ${
              view === "kanban" ? "bg-[var(--text)] text-[var(--bg)]" : ""
            }`}
          >
            <LayoutGrid size={14} style={{ color: view === "kanban" ? "var(--bg)" : "var(--text-light)" }} />
          </button>
          <button
            onClick={() => setView("table")}
            className={`p-1.5 rounded-full transition-all duration-300 ${
              view === "table" ? "bg-[var(--text)] text-[var(--bg)]" : ""
            }`}
          >
            <List size={14} style={{ color: view === "table" ? "var(--bg)" : "var(--text-light)" }} />
          </button>
        </div>
      </div>

      {/* Kanban View */}
      {view === "kanban" && !statusFilter && (
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
      {(view === "table" || statusFilter) && (
        <div className="card-static p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Name", "Company", "Status", "Priority", "Tasks", "Assets", "Deployed", "Updated"].map((h) => (
                    <th key={h} className="px-5 py-3.5 text-left text-[11px] font-medium tracking-wider uppercase whitespace-nowrap" style={{ color: "var(--text-light)" }}>
                      {h}
                    </th>
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
                        <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>{p.asset_count}</td>
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

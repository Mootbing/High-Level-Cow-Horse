"use client";

import { useState } from "react";
import { useEmails } from "@/lib/hooks/use-api";
import { StatusBadge } from "@/components/data/status-badge";
import { formatDate, truncate } from "@/lib/utils";
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from "lucide-react";

export default function EmailsPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const limit = 25;

  const { data, isLoading } = useEmails({
    offset: page * limit,
    limit,
    status: statusFilter,
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="space-y-4 animate-in">
      {/* Toolbar */}
      <div className="flex items-center gap-2 flex-wrap">
        {["all", "draft", "sent", "failed"].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s === "all" ? undefined : s); setPage(0); }}
            className={`text-xs px-3.5 py-1.5 rounded-full transition-all duration-300 ${
              (s === "all" && !statusFilter) || statusFilter === s
                ? "btn-primary"
                : "btn-outline"
            }`}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
        <span className="text-label ml-auto">
          {data?.total ?? 0} emails
        </span>
      </div>

      {/* Table */}
      <div className="card-static p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["", "To", "Subject", "Status", "Company", "Project", "Created", "Sent"].map((h) => (
                  <th key={h} className="px-5 py-3.5 text-left text-[11px] font-medium tracking-wider uppercase" style={{ color: "var(--text-light)" }}>{h}</th>
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
                : data?.items.map((e) => (
                    <>
                      <tr
                        key={e.id}
                        className="transition-colors duration-200 hover:bg-[var(--bg-alt)] cursor-pointer"
                        style={{ borderBottom: expandedId === e.id ? "none" : "1px solid var(--border)" }}
                        onClick={() => setExpandedId(expandedId === e.id ? null : e.id)}
                      >
                        <td className="px-3 py-3.5 w-8">
                          {expandedId === e.id
                            ? <ChevronUp size={14} style={{ color: "var(--text-light)" }} />
                            : <ChevronDown size={14} style={{ color: "var(--text-light)" }} />
                          }
                        </td>
                        <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text)" }}>{e.to_email}</td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text)" }}>{e.subject ? truncate(e.subject, 50) : "—"}</td>
                        <td className="px-5 py-3.5"><StatusBadge status={e.status} /></td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-muted)" }}>{e.prospect_company || "—"}</td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-muted)" }}>{e.project_name || "—"}</td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(e.created_at)}</td>
                        <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(e.sent_at)}</td>
                      </tr>
                      {expandedId === e.id && (
                        <tr key={`${e.id}-body`} style={{ borderBottom: "1px solid var(--border)" }}>
                          <td colSpan={8} className="px-8 py-5" style={{ backgroundColor: "var(--bg-alt)" }}>
                            <div className="max-w-2xl">
                              <p className="text-label mb-1.5">Subject</p>
                              <p className="text-sm mb-4" style={{ color: "var(--text)" }}>
                                {e.edited_subject || e.subject || "—"}
                              </p>
                              <p className="text-label mb-1.5">Body</p>
                              <pre className="text-sm whitespace-pre-wrap leading-relaxed" style={{ color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}>
                                {e.edited_body || e.body || "—"}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
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
    </div>
  );
}

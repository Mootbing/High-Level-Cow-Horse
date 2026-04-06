"use client";

import { useState } from "react";
import Link from "next/link";
import { useProspects } from "@/lib/hooks/use-api";
import { useSearch } from "@/lib/search-context";
import { ToolbarSlot } from "@/lib/toolbar-context";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { SortableHeader } from "@/components/data/sortable-header";
import { ExternalLink, ChevronLeft, ChevronRight, Check, Trash2 } from "lucide-react";

export default function ProspectsPage() {
  const { search } = useSearch();
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState("-created_at");
  const [showAll, setShowAll] = useState(false);
  const limit = 25;

  const { data, isLoading } = useProspects({
    offset: page * limit,
    limit,
    search: search || undefined,
    sort,
    prospects_only: !showAll || undefined,
  });

  const queryClient = useQueryClient();
  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete prospect "${name}"?`)) return;
    await api.deleteProspect(id);
    queryClient.invalidateQueries({ queryKey: ["prospects"] });
  }


  return (
    <div className="space-y-4 animate-in">
      <ToolbarSlot count={data?.total ?? 0}>
        <button
          onClick={() => { setShowAll(!showAll); setPage(0); }}
          className="flex items-center gap-2 text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          <span
            className="flex items-center justify-center w-4 h-4 rounded border transition-all duration-200"
            style={{
              borderColor: showAll ? "var(--accent)" : "var(--border)",
              backgroundColor: showAll ? "var(--accent)" : "transparent",
            }}
          >
            {showAll && <Check size={10} color="white" strokeWidth={3} />}
          </span>
          Show all
        </button>
      </ToolbarSlot>

      {/* Table */}
      <div className="card-static p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {[
                  { label: "Company", key: "company_name" },
                  { label: "URL", key: "url" },
                  { label: "Industry", key: "industry" },
                  { label: "Emails", key: null },
                  { label: "Phone", key: null },
                  { label: "Colors", key: null },
                  { label: "Problems", key: null },
                  { label: "Projects", key: null },
                  { label: "Scraped", key: "scraped_at" },
                ].map((col) => (
                  <SortableHeader key={col.label} label={col.label} sortKey={col.key} currentSort={sort} onSort={setSort} />
                ))}
                <th className="px-3 py-3.5 w-12" />
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 9 }).map((_, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      {Array.from({ length: 9 }).map((_, j) => (
                        <td key={j} className="px-5 py-3.5">
                          <div className="skeleton h-4 w-20" />
                        </td>
                      ))}
                    </tr>
                  ))
                : data?.items.map((p) => (
                    <tr
                      key={p.id}
                      className="transition-colors duration-200 hover:bg-[var(--bg-alt)] cursor-pointer"
                      style={{ borderBottom: "1px solid var(--border)" }}
                    >
                      <td className="px-5 py-3.5">
                        <Link
                          href={`/prospects/${p.id}`}
                          className="font-medium hover:text-[var(--accent)] transition-colors"
                          style={{ color: "var(--text)" }}
                        >
                          {p.company_name || "Unknown"}
                        </Link>
                      </td>
                      <td className="px-5 py-3.5">
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs font-data text-[var(--accent)] hover:underline"
                        >
                          {new URL(p.url).hostname}
                          <ExternalLink size={10} />
                        </a>
                      </td>
                      <td className="px-5 py-3.5">
                        {p.industry && (
                          <span
                            className="text-xs px-2.5 py-1 rounded-full"
                            style={{ backgroundColor: "var(--bg-alt)", color: "var(--text-muted)" }}
                          >
                            {p.industry}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-xs font-data" style={{ color: "var(--text-muted)" }}>
                        {p.contact_emails.length > 0 ? p.contact_emails[0] : "—"}
                      </td>
                      <td className="px-5 py-3.5 text-xs font-data" style={{ color: "var(--text-muted)" }}>
                        {p.phone_number || "—"}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex gap-1">
                          {(p.brand_colors || []).slice(0, 4).map((c, i) => (
                            <span
                              key={i}
                              className="w-4 h-4 rounded-full border"
                              style={{ backgroundColor: c, borderColor: "var(--border)" }}
                              title={c}
                            />
                          ))}
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>
                        {p.site_problems_count}
                      </td>
                      <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>
                        {p.project_count}
                      </td>
                      <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>
                        {formatDate(p.scraped_at)}
                      </td>
                      <td className="px-3 py-3.5">
                        {p.project_count === 0 && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(p.id, p.company_name || "Unknown"); }}
                            className="p-1.5 rounded-full hover:bg-red-50 transition-colors"
                            title="Delete prospect"
                          >
                            <Trash2 size={13} className="text-red-400" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div
            className="flex items-center justify-between px-5 py-3"
            style={{ borderTop: "1px solid var(--border)" }}
          >
            <span className="text-xs" style={{ color: "var(--text-light)" }}>
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-full hover:bg-[var(--bg-alt)] disabled:opacity-30 transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-full hover:bg-[var(--bg-alt)] disabled:opacity-30 transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

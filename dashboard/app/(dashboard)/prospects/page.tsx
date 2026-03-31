"use client";

import { useState } from "react";
import Link from "next/link";
import { useProspects } from "@/lib/hooks/use-api";
import { formatDate } from "@/lib/utils";
import { Search, ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";

export default function ProspectsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState("-created_at");
  const limit = 25;

  const { data, isLoading } = useProspects({
    offset: page * limit,
    limit,
    search: search || undefined,
    sort,
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  const toggleSort = (col: string) => {
    if (sort === col) setSort(`-${col}`);
    else if (sort === `-${col}`) setSort(col);
    else setSort(`-${col}`);
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sort === col) return <span className="ml-1 text-[var(--accent)]">&#9650;</span>;
    if (sort === `-${col}`) return <span className="ml-1 text-[var(--accent)]">&#9660;</span>;
    return null;
  };

  return (
    <div className="space-y-4 animate-in">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div
          className="flex items-center gap-2 px-4 py-2.5 rounded-full w-full sm:w-72 border transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_var(--accent-soft)]"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <Search size={14} style={{ color: "var(--text-light)" }} />
          <input
            type="text"
            placeholder="Search prospects..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            className="bg-transparent border-none outline-none text-sm flex-1"
            style={{ color: "var(--text)" }}
          />
        </div>
        <span className="text-label">
          {data?.total ?? 0} prospects
        </span>
      </div>

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
                  { label: "Colors", key: null },
                  { label: "Problems", key: null },
                  { label: "Projects", key: null },
                  { label: "Scraped", key: "scraped_at" },
                ].map((col) => (
                  <th
                    key={col.label}
                    className="px-5 py-3.5 text-left text-[11px] font-medium tracking-wider uppercase whitespace-nowrap"
                    style={{ color: "var(--text-light)" }}
                  >
                    {col.key ? (
                      <button
                        onClick={() => toggleSort(col.key)}
                        className="flex items-center hover:text-[var(--text)] transition-colors"
                      >
                        {col.label}
                        <SortIcon col={col.key} />
                      </button>
                    ) : (
                      col.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      {Array.from({ length: 8 }).map((_, j) => (
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

"use client";

import { useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import { useSearch } from "@/lib/search-context";
import { useToolbar } from "@/lib/toolbar-context";
import { NAV_LINKS } from "@/lib/constants";
import { Search, X } from "lucide-react";

const SEARCHABLE_PAGES = ["/", "/prospects", "/projects", "/emails", "/knowledge"];

export function Topbar() {
  const pathname = usePathname();
  const { search, setSearch } = useSearch();
  const { toolbarContent, titlePrefix } = useToolbar();
  const inputRef = useRef<HTMLInputElement>(null);

  const currentPage =
    NAV_LINKS.find((link) =>
      link.href === "/" ? pathname === "/" : pathname.startsWith(link.href)
    )?.label ?? "Dashboard";

  const showSearch = SEARCHABLE_PAGES.some((p) =>
    p === "/" ? pathname === "/" : pathname.startsWith(p)
  );

  // Cmd+K shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <header
      className="h-16 flex items-center justify-between px-6 border-b sticky top-0 z-20"
      style={{
        borderColor: "var(--border)",
        backgroundColor: "rgba(250, 250, 248, 0.9)",
        backdropFilter: "blur(16px) saturate(180%)",
        WebkitBackdropFilter: "blur(16px) saturate(180%)",
      }}
    >
      <div className="flex items-center gap-3">
        <h1
          className="text-lg tracking-tight"
          style={{
            fontFamily: "var(--font-serif)",
            color: "var(--text)",
            letterSpacing: "-0.02em",
          }}
        >
          {titlePrefix ? `${titlePrefix} ${currentPage}` : currentPage}
        </h1>
        {toolbarContent}
      </div>

      {showSearch && (
        <div
          className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full w-64 border transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_var(--accent-soft)]"
          style={{
            backgroundColor: "var(--bg-card)",
            borderColor: "var(--border)",
          }}
        >
          <Search size={16} style={{ color: "var(--text-light)", flexShrink: 0 }} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none outline-none text-[13px] flex-1"
            style={{ color: "var(--text)" }}
          />
          {search ? (
            <button onClick={() => setSearch("")} className="hover:text-[var(--text)] transition-colors" style={{ color: "var(--text-light)" }}>
              <X size={12} />
            </button>
          ) : (
            <kbd
              className="text-[10px] px-1.5 py-0.5 rounded font-mono"
              style={{
                backgroundColor: "var(--bg-alt)",
                color: "var(--text-light)",
              }}
            >
              &#8984;K
            </kbd>
          )}
        </div>
      )}
    </header>
  );
}

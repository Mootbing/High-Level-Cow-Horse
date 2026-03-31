"use client";

import { usePathname } from "next/navigation";
import { Search } from "lucide-react";
import { NAV_LINKS } from "@/lib/constants";

export function Topbar() {
  const pathname = usePathname();

  const currentPage =
    NAV_LINKS.find((link) =>
      link.href === "/" ? pathname === "/" : pathname.startsWith(link.href)
    )?.label ?? "Dashboard";

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
      <h1
        className="text-lg tracking-tight"
        style={{
          fontFamily: "var(--font-serif)",
          color: "var(--text)",
          letterSpacing: "-0.02em",
        }}
      >
        {currentPage}
      </h1>

      <div
        className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full w-64 border transition-all duration-300 focus-within:border-[var(--accent)] focus-within:shadow-[0_0_0_3px_var(--accent-soft)]"
        style={{
          backgroundColor: "var(--bg-card)",
          borderColor: "var(--border)",
          color: "var(--text-light)",
        }}
      >
        <Search size={14} />
        <span className="text-[13px]">Search...</span>
        <kbd
          className="ml-auto text-[10px] px-1.5 py-0.5 rounded font-mono"
          style={{
            backgroundColor: "var(--bg-alt)",
            color: "var(--text-light)",
          }}
        >
          &#8984;K
        </kbd>
      </div>
    </header>
  );
}

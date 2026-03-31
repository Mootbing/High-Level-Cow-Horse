"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { NAV_LINKS } from "@/lib/constants";
import { ChevronLeft } from "lucide-react";
import { useState } from "react";

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "hidden lg:flex flex-col sidebar h-screen sticky top-0 transition-all duration-300 z-30",
        collapsed ? "w-[68px]" : "w-[260px]"
      )}
    >
      {/* Logo */}
      <div
        className="flex items-center gap-3 px-5 h-16 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <span
          className="text-xl tracking-tight flex-shrink-0"
          style={{
            fontFamily: "var(--font-serif)",
            color: "var(--text)",
            letterSpacing: "-0.02em",
          }}
        >
          {collapsed ? "C" : "Clarmi"}
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {NAV_LINKS.map((link) => {
          const isActive =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-[12px] text-[13px] font-medium transition-all duration-300",
                isActive
                  ? "text-[var(--accent)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)]"
              )}
              style={
                isActive
                  ? { backgroundColor: "var(--accent-soft)" }
                  : undefined
              }
            >
              <link.icon size={18} className="flex-shrink-0" />
              {!collapsed && <span>{link.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mx-3 mb-4 flex items-center justify-center gap-2 px-3 py-2 rounded-[12px] text-xs font-medium transition-colors hover:bg-[var(--bg-alt)]"
        style={{ color: "var(--text-light)" }}
      >
        <ChevronLeft
          size={16}
          className={cn(
            "transition-transform duration-300",
            collapsed && "rotate-180"
          )}
        />
        {!collapsed && <span>Collapse</span>}
      </button>
    </aside>
  );
}

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { MOBILE_NAV_MAIN, MOBILE_NAV_MORE } from "@/lib/constants";
import { MoreHorizontal, X } from "lucide-react";

export function MobileNav() {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(false);

  // Close overlay on navigation
  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  const isMoreActive = MOBILE_NAV_MORE.some((link) =>
    pathname.startsWith(link.href)
  );

  return (
    <>
      {/* Overlay */}
      {moreOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40"
          style={{ backgroundColor: "rgba(0,0,0,0.4)" }}
          onClick={() => setMoreOpen(false)}
        >
          <div
            className="absolute bottom-16 left-0 right-0 rounded-t-2xl border-t overflow-hidden"
            style={{
              backgroundColor: "var(--bg-card)",
              borderColor: "var(--border)",
              boxShadow: "0 -8px 40px rgba(0,0,0,0.12)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 grid grid-cols-4 gap-2">
              {MOBILE_NAV_MORE.map((link) => {
                const isActive = pathname.startsWith(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "flex flex-col items-center gap-1.5 py-3 rounded-xl transition-colors duration-200",
                      isActive
                        ? "text-[var(--accent)] bg-[var(--accent-soft)]"
                        : "text-[var(--text-muted)] hover:bg-[var(--bg-alt)]"
                    )}
                  >
                    <link.icon size={22} />
                    <span className="text-[11px] font-medium">{link.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Bottom bar */}
      <nav
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around h-16 border-t"
        style={{
          backgroundColor: "rgba(250, 250, 248, 0.95)",
          backdropFilter: "blur(20px) saturate(180%)",
          WebkitBackdropFilter: "blur(20px) saturate(180%)",
          borderColor: "var(--border)",
        }}
      >
        {MOBILE_NAV_MAIN.map((link) => {
          const isActive =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex flex-col items-center gap-0.5 px-3 py-1.5 text-[10px] font-medium transition-colors duration-300",
                isActive
                  ? "text-[var(--accent)]"
                  : "text-[var(--text-light)]"
              )}
            >
              <link.icon size={20} />
              <span>{link.label}</span>
            </Link>
          );
        })}
        <button
          onClick={() => setMoreOpen(!moreOpen)}
          className={cn(
            "flex flex-col items-center gap-0.5 px-3 py-1.5 text-[10px] font-medium transition-colors duration-300",
            moreOpen || isMoreActive
              ? "text-[var(--accent)]"
              : "text-[var(--text-light)]"
          )}
        >
          {moreOpen ? <X size={20} /> : <MoreHorizontal size={20} />}
          <span>More</span>
        </button>
      </nav>
    </>
  );
}

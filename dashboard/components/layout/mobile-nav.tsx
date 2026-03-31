"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { MOBILE_NAV_LINKS } from "@/lib/constants";

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around h-16 border-t"
      style={{
        backgroundColor: "rgba(250, 250, 248, 0.95)",
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        borderColor: "var(--border)",
      }}
    >
      {MOBILE_NAV_LINKS.map((link) => {
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
    </nav>
  );
}

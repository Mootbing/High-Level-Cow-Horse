"use client";

import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color?: string;
  subtitle?: string;
}

export function StatCard({
  label,
  value,
  icon: Icon,
  color = "var(--accent)",
  subtitle,
}: StatCardProps) {
  return (
    <div className="card-static p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-label">{label}</span>
        <div
          className="w-9 h-9 rounded-[12px] flex items-center justify-center"
          style={{ backgroundColor: `${color}12` }}
        >
          <Icon size={17} style={{ color }} />
        </div>
      </div>
      <div>
        <span
          className="display-number text-3xl"
          style={{ color: "var(--text)" }}
        >
          {value}
        </span>
        {subtitle && (
          <p className="text-xs mt-1" style={{ color: "var(--text-light)" }}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}

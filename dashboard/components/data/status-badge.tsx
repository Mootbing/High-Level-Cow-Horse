"use client";

import { STATUS_COLORS, STATUS_LABELS } from "@/lib/constants";

export function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "#8e8e93";
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium tracking-wide"
      style={{
        backgroundColor: `${color}12`,
        color: color,
        border: `1px solid ${color}20`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  );
}

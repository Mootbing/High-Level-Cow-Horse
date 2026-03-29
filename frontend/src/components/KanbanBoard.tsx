import type { KanbanColumn as KanbanColumnType } from "../types";
import KanbanColumn from "./KanbanColumn";

const COLUMN_COLORS: Record<string, string> = {
  pending: "border-t-muted-foreground/30",
  in_progress: "border-t-[#fbbf24]",
  review: "border-t-[#a78bfa]",
  completed: "border-t-[#4ade80]",
  failed: "border-t-[#f87171]",
};

export default function KanbanBoard({ columns }: { columns: KanbanColumnType[] }) {
  return (
    <div className="grid grid-cols-5 gap-4 min-h-[60vh]">
      {columns.map((col) => (
        <KanbanColumn
          key={col.status}
          column={col}
          accentClass={COLUMN_COLORS[col.status] || "border-t-border"}
        />
      ))}
    </div>
  );
}

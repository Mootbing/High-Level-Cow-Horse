import type { KanbanColumn as KanbanColumnType } from "../types";
import KanbanCard from "./KanbanCard";
import { cn } from "@/lib/utils";

export default function KanbanColumn({
  column,
  accentClass,
}: {
  column: KanbanColumnType;
  accentClass: string;
}) {
  return (
    <div className={cn("bg-card/50 rounded-lg border border-border border-t-2", accentClass)}>
      <div className="p-3 border-b border-border">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-foreground">{column.label}</span>
          <span className="text-xs bg-accent px-2 py-0.5 rounded-full text-muted-foreground">
            {column.count}
          </span>
        </div>
      </div>
      <div className="p-2 space-y-2 max-h-[70vh] overflow-y-auto">
        {column.cards.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-4">No tasks</p>
        ) : (
          column.cards.map((card) => <KanbanCard key={card.id} card={card} />)
        )}
      </div>
    </div>
  );
}

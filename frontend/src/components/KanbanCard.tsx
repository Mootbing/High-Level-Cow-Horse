import type { KanbanTaskCard } from "../types";
import { Badge } from "./ui/badge";
import { cn } from "@/lib/utils";

const AGENT_COLORS: Record<string, string> = {
  ceo: "border-l-blue-500",
  project_manager: "border-l-purple-500",
  inbound: "border-l-cyan-500",
  outbound: "border-l-orange-500",
  designer: "border-l-pink-500",
  engineer: "border-l-green-500",
  qa: "border-l-yellow-500",
  reviewer: "border-l-amber-500",
  client_comms: "border-l-teal-500",
  research: "border-l-indigo-500",
  learning: "border-l-slate-400",
};

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function KanbanCard({ card }: { card: KanbanTaskCard }) {
  const borderColor = AGENT_COLORS[card.agent_type] || "border-l-border";
  const time = card.completed_at || card.started_at || card.created_at;

  return (
    <div
      className={cn(
        "bg-background border border-border rounded-md p-3 border-l-2",
        borderColor
      )}
    >
      <div className="flex items-center justify-between mb-1.5">
        <Badge variant="secondary" className="text-[10px] font-mono">
          {card.agent_type}
        </Badge>
        <span className="text-[10px] text-muted-foreground">{timeAgo(time)}</span>
      </div>

      <p className="text-sm text-foreground leading-tight mb-2 line-clamp-2">
        {card.title}
      </p>

      <div className="space-y-1 text-[10px] text-muted-foreground">
        {card.delegated_by && (
          <div>
            <span className="text-muted-foreground/60">from </span>
            <span>{card.delegated_by}</span>
          </div>
        )}
        {card.project_name && (
          <div>
            <span className="text-muted-foreground/60">project </span>
            <span>{card.project_name}</span>
          </div>
        )}
        {card.error && (
          <div className="text-[#f87171] line-clamp-1">{card.error}</div>
        )}
      </div>
    </div>
  );
}

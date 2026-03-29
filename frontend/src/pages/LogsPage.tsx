import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AgentLogEntry } from "../types";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Select } from "../components/ui/select";
import { cn } from "@/lib/utils";

const AGENT_TYPES = [
  "",
  "ceo",
  "project_manager",
  "inbound",
  "outbound",
  "designer",
  "engineer",
  "qa",
  "client_comms",
  "research",
  "learning",
];

export default function LogsPage() {
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [filter, setFilter] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    api.agentLogs(filter || undefined, 200).then(setLogs).catch(() => {});
  }, [filter]);

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-foreground">Agent Logs</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{logs.length} entries</span>
          <Select value={filter} onChange={(e) => setFilter(e.target.value)}>
            {AGENT_TYPES.map((a) => (
              <option key={a} value={a}>
                {a || "All agents"}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {logs.length === 0 ? (
        <p className="text-muted-foreground">
          No agent logs yet. Logs appear here as agents process tasks.
        </p>
      ) : (
        <div className="space-y-1">
          {logs.map((log) => {
            const isExpanded = expanded.has(log.id);
            const preview = log.content.slice(0, 150);
            const hasMore = log.content.length > 150;

            return (
              <Card
                key={log.id}
                className={cn(
                  "px-4 py-3 cursor-pointer hover:bg-accent/30 transition-colors",
                  isExpanded && "bg-accent/20"
                )}
                onClick={() => toggleExpand(log.id)}
              >
                <div className="flex items-center gap-3 mb-1">
                  <Badge variant="secondary" className="text-[10px] font-mono">
                    {log.agent_type}
                  </Badge>
                  <Badge
                    variant={log.role === "assistant" ? "info" : "outline"}
                    className="text-[10px]"
                  >
                    {log.role}
                  </Badge>
                  {log.token_count && (
                    <span className="text-[10px] text-muted-foreground">
                      {log.token_count} tokens
                    </span>
                  )}
                  <span className="text-[10px] text-muted-foreground ml-auto">
                    {log.created_at
                      ? new Date(log.created_at).toLocaleString()
                      : ""}
                  </span>
                </div>
                <div
                  className={cn(
                    "text-sm text-muted-foreground font-mono whitespace-pre-wrap",
                    !isExpanded && "line-clamp-2"
                  )}
                >
                  {isExpanded ? log.content : preview}
                  {!isExpanded && hasMore && (
                    <span className="text-foreground/30"> ...</span>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { AgentLogEntry, ProjectSummary } from "../types";
import { cn, parseUTC } from "@/lib/utils";
import {
  Terminal,
  ChevronDown,
  Search,
  X,
} from "lucide-react";

const AGENT_COLORS: Record<string, string> = {
  ceo: "#3b82f6",
  project_manager: "#a855f7",
  inbound: "#06b6d4",
  outbound: "#f97316",
  designer: "#ec4899",
  engineer: "#22c55e",
  qa: "#eab308",
  reviewer: "#f59e0b",
  client_comms: "#14b8a6",
  research: "#6366f1",
  learning: "#94a3b8",
};

const AGENT_BG_COLORS: Record<string, string> = {
  ceo: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  project_manager: "bg-purple-500/15 text-purple-400 border-purple-500/20",
  inbound: "bg-cyan-500/15 text-cyan-400 border-cyan-500/20",
  outbound: "bg-orange-500/15 text-orange-400 border-orange-500/20",
  designer: "bg-pink-500/15 text-pink-400 border-pink-500/20",
  engineer: "bg-green-500/15 text-green-400 border-green-500/20",
  qa: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
  reviewer: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  client_comms: "bg-teal-500/15 text-teal-400 border-teal-500/20",
  research: "bg-indigo-500/15 text-indigo-400 border-indigo-500/20",
  learning: "bg-slate-500/15 text-slate-400 border-slate-500/20",
};

function formatTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = parseUTC(dateStr);
  if (!d) return "";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = parseUTC(dateStr);
  if (!d) return "";
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = parseUTC(dateStr);
  if (!d) return "";
  return `${d.toLocaleDateString([], { month: "short", day: "numeric" })} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [agentFilter, setAgentFilter] = useState<string>("all");
  const [projectFilter, setProjectFilter] = useState<string>("all");
  const [searchText, setSearchText] = useState("");
  const [groupByProject, setGroupByProject] = useState(false);
  const [expandedContent, setExpandedContent] = useState<Set<string>>(new Set());

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchLogs = useCallback(() => {
    const opts: { agentType?: string; projectId?: string; limit?: number } = { limit: 500 };
    if (agentFilter !== "all") opts.agentType = agentFilter;
    if (projectFilter !== "all") opts.projectId = projectFilter;
    api.allAgentLogs(opts).then((data) => {
      setLogs(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [agentFilter, projectFilter]);

  const fetchProjects = useCallback(() => {
    api.projects().then(setProjects).catch(() => {});
  }, []);

  // Initial load
  useEffect(() => {
    fetchLogs();
    fetchProjects();
  }, [fetchLogs, fetchProjects]);

  // Polling every 5 seconds
  useEffect(() => {
    pollRef.current = setInterval(fetchLogs, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchLogs]);

  // Get unique agent types from current logs
  const agentTypes = useMemo(() => {
    const types = new Set(logs.map((l) => l.agent_type));
    return [...types].sort();
  }, [logs]);

  // Build project lookup
  const projectMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of projects) {
      map[p.id] = p.name;
    }
    return map;
  }, [projects]);

  // Apply search filter
  const filteredLogs = useMemo(() => {
    if (!searchText.trim()) return logs;
    const term = searchText.toLowerCase();
    return logs.filter(
      (l) =>
        l.content.toLowerCase().includes(term) ||
        l.agent_type.toLowerCase().includes(term) ||
        l.role.toLowerCase().includes(term)
    );
  }, [logs, searchText]);

  // Group by project
  const groupedLogs = useMemo(() => {
    if (!groupByProject) return null;
    const groups: Record<string, AgentLogEntry[]> = {};
    for (const log of filteredLogs) {
      const key = log.project_id ?? "__no_project__";
      if (!groups[key]) groups[key] = [];
      groups[key].push(log);
    }
    // Sort groups by most recent log entry
    const sorted = Object.entries(groups).sort((a, b) => {
      const aTime = a[1][0]?.created_at ?? "";
      const bTime = b[1][0]?.created_at ?? "";
      return bTime.localeCompare(aTime);
    });
    return sorted;
  }, [filteredLogs, groupByProject]);

  const toggleExpand = (id: string) => {
    setExpandedContent((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const renderLogEntry = (log: AgentLogEntry) => {
    const isExpanded = expandedContent.has(log.id);
    const isLong = log.content.length > 300;
    const displayContent = isLong && !isExpanded
      ? log.content.slice(0, 300) + "..."
      : log.content;

    return (
      <div
        key={log.id}
        className="flex gap-2 hover:bg-white/[0.02] px-2 py-1 rounded group"
      >
        {/* Timestamp */}
        <span className="text-muted-foreground/40 shrink-0 w-[130px] text-right tabular-nums">
          {formatDateTime(log.created_at)}
        </span>

        {/* Agent badge */}
        <span className="shrink-0 w-[120px] text-right">
          <span
            className={cn(
              "inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold border",
              AGENT_BG_COLORS[log.agent_type] ?? "bg-white/5 text-muted-foreground border-white/10",
            )}
          >
            {log.agent_type}
          </span>
        </span>

        {/* Role */}
        <span
          className={cn(
            "shrink-0 w-[55px] text-right text-[11px] font-medium",
            log.role === "assistant"
              ? "text-[#c084fc]"
              : log.role === "user"
                ? "text-[#60a5fa]"
                : log.role === "tool"
                  ? "text-[#f472b6]"
                  : "text-muted-foreground/50",
          )}
        >
          {log.role}
        </span>

        {/* Project indicator (when not grouping) */}
        {!groupByProject && log.project_id && (
          <span className="shrink-0 text-[10px] text-muted-foreground/30 w-[100px] truncate text-right" title={projectMap[log.project_id] ?? log.project_id}>
            {projectMap[log.project_id] ?? log.project_id.slice(0, 8)}
          </span>
        )}

        {/* Content */}
        <span
          className={cn(
            "text-foreground/80 break-all whitespace-pre-wrap leading-relaxed",
            isLong && "cursor-pointer",
          )}
          onClick={isLong ? () => toggleExpand(log.id) : undefined}
        >
          {displayContent}
          {isLong && !isExpanded && (
            <button className="text-muted-foreground/40 hover:text-muted-foreground ml-1 text-[10px]">
              show more
            </button>
          )}
        </span>
      </div>
    );
  };

  return (
    <div className="p-8 max-w-[1800px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Terminal className="w-5 h-5 text-muted-foreground" />
          <h2 className="text-xl font-bold text-foreground">General Logs</h2>
          <span className="text-sm text-muted-foreground tabular-nums">
            {filteredLogs.length} entries
          </span>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4ade80] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#4ade80]" />
          </span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        {/* Agent type filter */}
        <div className="relative">
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="appearance-none bg-background border border-border rounded-md px-3 py-1.5 pr-7 text-xs text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-white/20"
          >
            <option value="all">All agents</option>
            {agentTypes.map((at) => (
              <option key={at} value={at}>
                {at}
              </option>
            ))}
          </select>
          <ChevronDown className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        </div>

        {/* Project filter */}
        <div className="relative">
          <select
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="appearance-none bg-background border border-border rounded-md px-3 py-1.5 pr-7 text-xs text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-white/20"
          >
            <option value="all">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <ChevronDown className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        </div>

        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search logs..."
            className="w-full bg-background border border-border rounded-md pl-8 pr-8 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-white/20"
          />
          {searchText && (
            <button
              onClick={() => setSearchText("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Group by project toggle */}
        <button
          onClick={() => setGroupByProject(!groupByProject)}
          className={cn(
            "text-xs px-3 py-1.5 rounded-md border transition-colors",
            groupByProject
              ? "bg-blue-500/10 border-blue-500/30 text-blue-400"
              : "bg-background border-border text-muted-foreground hover:text-foreground",
          )}
        >
          Group by project
        </button>
      </div>

      {/* Log console */}
      <div className="bg-[#0a0a0a] border border-border rounded-lg overflow-hidden font-mono">
        {/* Console header bar */}
        <div className="flex items-center gap-1.5 px-4 py-2 bg-white/[0.02] border-b border-border">
          <span className="w-2.5 h-2.5 rounded-full bg-[#f87171]" />
          <span className="w-2.5 h-2.5 rounded-full bg-[#fbbf24]" />
          <span className="w-2.5 h-2.5 rounded-full bg-[#4ade80]" />
          <span className="text-[10px] text-muted-foreground ml-2">
            general-logs &mdash; all agents &mdash; auto-refresh 5s
          </span>
        </div>

        {/* Log entries */}
        <div className="max-h-[calc(100vh-280px)] overflow-y-auto p-3 space-y-0.5 text-xs leading-relaxed">
          {loading ? (
            <div className="text-muted-foreground/50 py-8 text-center text-sm">
              Loading logs...
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-muted-foreground/50 py-8 text-center text-sm">
              No logs found.
              {(agentFilter !== "all" || projectFilter !== "all" || searchText) && (
                <button
                  onClick={() => { setAgentFilter("all"); setProjectFilter("all"); setSearchText(""); }}
                  className="ml-2 text-blue-400 hover:underline"
                >
                  Clear filters
                </button>
              )}
            </div>
          ) : groupByProject && groupedLogs ? (
            // Grouped view
            groupedLogs.map(([projId, projLogs]) => (
              <div key={projId} className="mb-4">
                <div className="sticky top-0 bg-[#0a0a0a] z-10 flex items-center gap-2 py-1.5 px-2 border-b border-white/5 mb-1">
                  <span className="text-[11px] font-semibold text-foreground/70">
                    {projId === "__no_project__"
                      ? "No Project"
                      : projectMap[projId] ?? projId.slice(0, 8)}
                  </span>
                  <span className="text-[10px] text-muted-foreground/40">
                    ({projLogs.length} entries)
                  </span>
                </div>
                {projLogs.map(renderLogEntry)}
              </div>
            ))
          ) : (
            // Flat chronological view (newest first, as returned by API)
            filteredLogs.map(renderLogEntry)
          )}
        </div>
      </div>
    </div>
  );
}

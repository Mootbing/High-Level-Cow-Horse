import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type {
  ProjectDetail,
  KanbanBoardResponse,
  AgentLogEntry,
  AgentsStatusResponse,
} from "../types";
import StatusBadge from "../components/StatusBadge";
import KanbanBoard from "../components/KanbanBoard";
import { Button } from "../components/ui/button";
import {
  ArrowLeft,
  ExternalLink,
  Trash2,
  Terminal,
  Activity,
  ChevronDown,
} from "lucide-react";
import ProjectPipelineBar from "../components/ProjectPipelineBar";

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

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [board, setBoard] = useState<KanbanBoardResponse | null>(null);
  const [agents, setAgents] = useState<AgentsStatusResponse | null>(null);
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [deleting, setDeleting] = useState(false);
  const [logAutoScroll, setLogAutoScroll] = useState(true);
  const [logFilter, setLogFilter] = useState<string>("all");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchBoard = useCallback(() => {
    if (id) {
      api.kanbanProject(id).then(setBoard).catch(() => {});
    }
  }, [id]);

  const fetchLogs = useCallback(() => {
    if (id) {
      api.agentLogsByProject(id, 200).then(setLogs).catch(() => {});
    }
  }, [id]);

  const fetchAgents = useCallback(() => {
    api.agentsStatus().then(setAgents).catch(() => {});
  }, []);

  useEffect(() => {
    if (id) {
      api.project(id).then(setProject).catch(() => {});
      fetchBoard();
      fetchLogs();
      fetchAgents();
    }
  }, [id, fetchBoard, fetchLogs, fetchAgents]);

  // Poll everything every 5s
  useEffect(() => {
    pollRef.current = setInterval(() => {
      fetchBoard();
      fetchLogs();
      fetchAgents();
      if (id) api.project(id).then(setProject).catch(() => {});
    }, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchBoard, fetchLogs, fetchAgents, id]);

  // Auto-scroll logs
  useEffect(() => {
    if (logAutoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, logAutoScroll]);

  if (!project) {
    return (
      <div className="p-8 text-muted-foreground">Loading...</div>
    );
  }

  // Compute task stats
  const totalTasks = board?.total_tasks ?? project.tasks.length;
  const completedTasks =
    board?.columns.find((c) => c.status === "completed")?.count ??
    project.tasks.filter((t) => t.status === "completed").length;
  const inProgressTasks =
    board?.columns.find((c) => c.status === "in_progress")?.count ?? 0;
  const failedTasks =
    board?.columns.find((c) => c.status === "failed")?.count ?? 0;

  // Active agents on this project — agents that are alive and busy
  const activeAgents = agents?.agents.filter(
    (a) => a.status === "alive" && a.current_task
  ) ?? [];

  // Unique agent types from project tasks for log filtering
  const agentTypesInProject = [
    ...new Set(
      (board?.columns.flatMap((c) => c.cards.map((card) => card.agent_type)) ?? [])
    ),
  ].sort();

  // Filtered logs
  const filteredLogs = logFilter === "all"
    ? logs
    : logs.filter((l) => l.agent_type === logFilter);

  // Reverse to show oldest first (chronological) in the console
  const chronologicalLogs = [...filteredLogs].reverse();

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      {/* Navigation */}
      <Link to="/projects">
        <Button
          variant="ghost"
          size="sm"
          className="mb-4 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to projects
        </Button>
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-foreground">{project.name}</h2>
          <StatusBadge status={project.status} />
          {project.deployed_url && (
            <a
              href={project.deployed_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-foreground/50 hover:text-foreground text-sm hover:underline"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              {project.deployed_url}
            </a>
          )}
        </div>
        <Button
          variant="destructive"
          size="sm"
          disabled={deleting}
          onClick={async () => {
            if (!confirm("Delete this project? This will also remove the GitHub repo and Vercel project.")) return;
            setDeleting(true);
            try {
              await api.deleteProject(project.id);
              navigate("/projects");
            } catch {
              setDeleting(false);
            }
          }}
        >
          <Trash2 className="w-4 h-4 mr-1" />
          {deleting ? "Deleting..." : "Delete"}
        </Button>
      </div>

      {project.brief && (
        <p className="text-muted-foreground mb-6 max-w-3xl leading-relaxed">{project.brief}</p>
      )}

      {/* Big Pipeline Progress Bar */}
      <ProjectPipelineBar
        status={project.status}
        completedTasks={completedTasks}
        totalTasks={totalTasks}
      />

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-card/50 border border-border rounded-lg p-4">
          <div className="text-2xl font-bold text-foreground tabular-nums">{totalTasks}</div>
          <div className="text-xs text-muted-foreground mt-1">Total Tasks</div>
        </div>
        <div className="bg-card/50 border border-border rounded-lg p-4">
          <div className="text-2xl font-bold text-[#fbbf24] tabular-nums">{inProgressTasks}</div>
          <div className="text-xs text-muted-foreground mt-1">In Progress</div>
        </div>
        <div className="bg-card/50 border border-border rounded-lg p-4">
          <div className="text-2xl font-bold text-[#4ade80] tabular-nums">{completedTasks}</div>
          <div className="text-xs text-muted-foreground mt-1">Completed</div>
        </div>
        <div className="bg-card/50 border border-border rounded-lg p-4">
          <div className="text-2xl font-bold text-[#f87171] tabular-nums">{failedTasks}</div>
          <div className="text-xs text-muted-foreground mt-1">Failed</div>
        </div>
      </div>

      {/* Active Agents Banner */}
      {activeAgents.length > 0 && (
        <div className="mb-6 bg-card/50 border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-[#4ade80]" />
            <span className="text-sm font-semibold text-foreground">
              Active Agents ({activeAgents.length})
            </span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4ade80] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#4ade80]" />
            </span>
          </div>
          <div className="flex flex-wrap gap-3">
            {activeAgents.map((agent) => (
              <div
                key={agent.agent_type}
                className="flex items-center gap-2 bg-background/50 border border-white/5 rounded-md px-3 py-2"
              >
                <div
                  className="w-2 h-2 rounded-full animate-pulse"
                  style={{ background: AGENT_COLORS[agent.agent_type] ?? "#888" }}
                />
                <span
                  className="text-xs font-mono font-semibold"
                  style={{ color: AGENT_COLORS[agent.agent_type] ?? "#888" }}
                >
                  {agent.agent_type}
                </span>
                {agent.current_task && (
                  <span className="text-xs text-muted-foreground max-w-[250px] truncate">
                    {agent.current_task}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Task Board */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Task Board</h3>
        {board && (
          <span className="text-sm text-muted-foreground tabular-nums">
            {board.total_tasks} tasks
          </span>
        )}
      </div>

      {board ? (
        <KanbanBoard columns={board.columns} />
      ) : (
        <p className="text-muted-foreground text-sm">Loading board...</p>
      )}

      {/* Agent Log Console */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold text-foreground">Agent Logs</h3>
            <span className="text-xs text-muted-foreground tabular-nums">
              ({filteredLogs.length} entries)
            </span>
          </div>
          <div className="flex items-center gap-3">
            {/* Agent filter */}
            <div className="relative">
              <select
                value={logFilter}
                onChange={(e) => setLogFilter(e.target.value)}
                className="appearance-none bg-background border border-border rounded-md px-3 py-1.5 pr-7 text-xs text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-white/20"
              >
                <option value="all">All agents</option>
                {agentTypesInProject.map((at) => (
                  <option key={at} value={at}>
                    {at}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
            </div>
            {/* Auto-scroll toggle */}
            <button
              onClick={() => setLogAutoScroll(!logAutoScroll)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${
                logAutoScroll
                  ? "bg-[#4ade80]/10 border-[#4ade80]/30 text-[#4ade80]"
                  : "bg-background border-border text-muted-foreground"
              }`}
            >
              Auto-scroll {logAutoScroll ? "ON" : "OFF"}
            </button>
          </div>
        </div>

        <div className="bg-[#0a0a0a] border border-border rounded-lg overflow-hidden font-mono">
          {/* Console header bar */}
          <div className="flex items-center gap-1.5 px-4 py-2 bg-white/[0.02] border-b border-border">
            <span className="w-2.5 h-2.5 rounded-full bg-[#f87171]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#fbbf24]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#4ade80]" />
            <span className="text-[10px] text-muted-foreground ml-2">
              agent-logs &mdash; {project.name}
            </span>
          </div>

          {/* Log entries */}
          <div className="max-h-[400px] overflow-y-auto p-3 space-y-0.5 text-xs leading-relaxed">
            {chronologicalLogs.length === 0 ? (
              <div className="text-muted-foreground/50 py-8 text-center text-sm">
                No agent logs for this project yet.
              </div>
            ) : (
              chronologicalLogs.map((log) => (
                <div key={log.id} className="flex gap-2 hover:bg-white/[0.02] px-1 py-0.5 rounded">
                  <span className="text-muted-foreground/40 shrink-0 w-[70px] text-right">
                    {formatTime(log.created_at)}
                  </span>
                  <span
                    className="shrink-0 w-[110px] text-right font-semibold"
                    style={{ color: AGENT_COLORS[log.agent_type] ?? "#888" }}
                  >
                    {log.agent_type}
                  </span>
                  <span
                    className={`shrink-0 w-[50px] text-right ${
                      log.role === "assistant"
                        ? "text-[#c084fc]"
                        : log.role === "user"
                          ? "text-[#60a5fa]"
                          : "text-muted-foreground/50"
                    }`}
                  >
                    {log.role}
                  </span>
                  <span className="text-foreground/80 break-all">
                    {log.content.length > 500
                      ? log.content.slice(0, 500) + "..."
                      : log.content}
                  </span>
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

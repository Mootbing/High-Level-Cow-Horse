import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { AgentLogEntry, AgentsStatusResponse, AgentStatus } from "../types";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

// --- Org hierarchy ---
const HIERARCHY: Record<string, string[]> = {
  ceo: ["project_manager", "inbound", "outbound", "client_comms", "research", "learning"],
  project_manager: ["designer", "engineer", "qa", "reviewer"],
};

const LABELS: Record<string, string> = {
  ceo: "CEO",
  project_manager: "PM",
  inbound: "Inbound",
  outbound: "Outbound",
  client_comms: "Comms",
  research: "Research",
  learning: "Learning",
  designer: "Designer",
  engineer: "Engineer",
  qa: "QA",
  reviewer: "Reviewer",
};

// --- Tree layout calculation ---
const NODE_W = 128;
const NODE_H = 56;
const H_GAP = 20;
const V_GAP = 64;

function computeLayout(): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};

  function subtreeWidth(node: string): number {
    const children = HIERARCHY[node];
    if (!children?.length) return NODE_W;
    const childrenW = children.reduce((s, c) => s + subtreeWidth(c), 0);
    return childrenW + (children.length - 1) * H_GAP;
  }

  function layout(node: string, cx: number, y: number) {
    const children = HIERARCHY[node];
    if (!children?.length) {
      positions[node] = { x: cx, y };
      return;
    }
    const totalW = subtreeWidth(node);
    let startX = cx - totalW / 2;
    for (const child of children) {
      const cw = subtreeWidth(child);
      layout(child, startX + cw / 2, y + NODE_H + V_GAP);
      startX += cw + H_GAP;
    }
    const first = positions[children[0]];
    const last = positions[children[children.length - 1]];
    positions[node] = { x: (first.x + last.x) / 2, y };
  }

  layout("ceo", 0, 0);

  // Normalize so min x/y = 0
  let minX = Infinity, minY = Infinity;
  for (const p of Object.values(positions)) {
    if (p.x < minX) minX = p.x;
    if (p.y < minY) minY = p.y;
  }
  for (const p of Object.values(positions)) {
    p.x -= minX;
    p.y -= minY;
  }
  return positions;
}

const BASE_POSITIONS = computeLayout();

// Collect edges for SVG lines
type Edge = { from: string; to: string };
function collectEdges(): Edge[] {
  const edges: Edge[] = [];
  for (const [parent, children] of Object.entries(HIERARCHY)) {
    for (const child of children) {
      edges.push({ from: parent, to: child });
    }
  }
  return edges;
}
const EDGES = collectEdges();

function agentState(a: AgentStatus): "busy" | "idle" | "offline" {
  if (a.status !== "alive") return "offline";
  if (a.queue_depth > 0 || a.current_task) return "busy";
  return "idle";
}

const STATE_COLORS = {
  idle: "bg-emerald-400",
  busy: "bg-amber-400",
  offline: "bg-red-400",
} as const;

const STATE_LABELS = {
  idle: "Idle",
  busy: "Busy",
  offline: "Offline",
} as const;

// --- Main Component ---
export default function AgentsPage() {
  const [data, setData] = useState<AgentsStatusResponse | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [dragOffsets, setDragOffsets] = useState<Record<string, { x: number; y: number }>>({});
  const dragging = useRef<{ agent: string; startX: number; startY: number; ox: number; oy: number } | null>(null);
  const didDrag = useRef(false);

  // Load agents status
  const load = useCallback(() => {
    api.agentsStatus().then(setData).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 10_000);
    return () => clearInterval(iv);
  }, [load]);

  // Load logs when agent is selected
  useEffect(() => {
    if (!selected) return;
    setLogsLoading(true);
    api.agentLogs(selected, 30).then((l) => {
      setLogs(l);
      setLogsLoading(false);
    }).catch(() => setLogsLoading(false));

    const iv = setInterval(() => {
      api.agentLogs(selected, 30).then(setLogs).catch(() => {});
    }, 5_000);
    return () => clearInterval(iv);
  }, [selected]);

  // Build agent lookup
  const agentMap: Record<string, AgentStatus> = {};
  if (data) {
    for (const a of data.agents) agentMap[a.agent_type] = a;
  }

  // Drag handlers
  const onMouseDown = (agent: string, e: React.MouseEvent) => {
    e.preventDefault();
    const off = dragOffsets[agent] ?? { x: 0, y: 0 };
    dragging.current = { agent, startX: e.clientX, startY: e.clientY, ox: off.x, oy: off.y };
    didDrag.current = false;

    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const dx = ev.clientX - dragging.current.startX;
      const dy = ev.clientY - dragging.current.startY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) didDrag.current = true;
      setDragOffsets((prev) => ({
        ...prev,
        [dragging.current!.agent]: { x: dragging.current!.ox + dx, y: dragging.current!.oy + dy },
      }));
    };
    const onUp = () => {
      dragging.current = null;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  };

  // Calculate final positions (base + drag offset)
  const pos = (agent: string) => {
    const base = BASE_POSITIONS[agent] ?? { x: 0, y: 0 };
    const off = dragOffsets[agent] ?? { x: 0, y: 0 };
    return { x: base.x + off.x, y: base.y + off.y };
  };

  // Canvas dimensions
  let maxX = 0, maxY = 0;
  for (const agent of Object.keys(BASE_POSITIONS)) {
    const p = pos(agent);
    if (p.x + NODE_W > maxX) maxX = p.x + NODE_W;
    if (p.y + NODE_H > maxY) maxY = p.y + NODE_H;
  }
  const canvasW = maxX + 80;
  const canvasH = maxY + 80;

  return (
    <div className="h-full flex">
      {/* Org chart area */}
      <div className="flex-1 overflow-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-foreground">Agents</h2>
          {data && (
            <span className="text-sm text-muted-foreground">
              {data.agents.filter((a) => a.status === "alive").length} online
              {data.total_pending > 0 && (
                <span className="ml-2 text-amber-400">{data.total_pending} queued</span>
              )}
            </span>
          )}
        </div>

        <div className="relative" style={{ width: canvasW, height: canvasH, minWidth: canvasW }}>
          {/* SVG connection lines */}
          <svg
            className="absolute inset-0 pointer-events-none"
            width={canvasW}
            height={canvasH}
          >
            {EDGES.map(({ from, to }) => {
              const fp = pos(from);
              const tp = pos(to);
              const x1 = fp.x + NODE_W / 2;
              const y1 = fp.y + NODE_H;
              const x2 = tp.x + NODE_W / 2;
              const y2 = tp.y;
              const midY = y1 + V_GAP / 2;
              return (
                <path
                  key={`${from}-${to}`}
                  d={`M${x1},${y1} L${x1},${midY} L${x2},${midY} L${x2},${y2}`}
                  fill="none"
                  stroke="hsl(0 0% 18%)"
                  strokeWidth={1.5}
                />
              );
            })}
          </svg>

          {/* Agent nodes */}
          {Object.keys(BASE_POSITIONS).map((agent) => {
            const a = agentMap[agent];
            const p = pos(agent);
            const state = a ? agentState(a) : "offline";

            return (
              <div
                key={agent}
                className={cn(
                  "absolute select-none rounded-xl border px-3 py-2 cursor-grab active:cursor-grabbing transition-shadow",
                  "bg-card hover:bg-accent/40",
                  selected === agent && "ring-1 ring-ring bg-accent/30",
                )}
                style={{
                  left: p.x,
                  top: p.y,
                  width: NODE_W,
                  height: NODE_H,
                }}
                onMouseDown={(e) => onMouseDown(agent, e)}
                onClick={() => { if (!didDrag.current) setSelected(selected === agent ? null : agent); }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "w-2 h-2 rounded-full shrink-0",
                      STATE_COLORS[state],
                      state === "busy" && "animate-pulse",
                    )}
                  />
                  <span className="text-sm font-medium text-foreground truncate">
                    {LABELS[agent] ?? agent}
                  </span>
                </div>
                <p className="text-[10px] text-muted-foreground truncate mt-0.5 pl-4">
                  {state === "busy" && a?.current_task
                    ? a.current_task
                    : STATE_LABELS[state]}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-96 border-l border-border bg-card flex flex-col h-full shrink-0">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <div className="flex items-center gap-2">
              {(() => {
                const a = agentMap[selected];
                const state = a ? agentState(a) : "offline";
                return (
                  <span
                    className={cn(
                      "w-2.5 h-2.5 rounded-full",
                      STATE_COLORS[state],
                      state === "busy" && "animate-pulse",
                    )}
                  />
                );
              })()}
              <h3 className="font-semibold text-foreground">
                {LABELS[selected] ?? selected}
              </h3>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-muted-foreground hover:text-foreground"
            >
              <X size={16} />
            </button>
          </div>

          {/* Agent meta */}
          {agentMap[selected] && (
            <div className="p-4 border-b border-border space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <span
                  className={cn(
                    agentMap[selected].status === "alive"
                      ? "text-emerald-400"
                      : "text-red-400",
                  )}
                >
                  {agentMap[selected].status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tier</span>
                <span className="text-foreground/70">{agentMap[selected].tier}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Queue</span>
                <span
                  className={cn(
                    agentMap[selected].queue_depth > 0
                      ? "text-amber-400"
                      : "text-foreground/70",
                  )}
                >
                  {agentMap[selected].queue_depth}
                </span>
              </div>
              {agentMap[selected].current_task && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Task</span>
                  <span className="text-foreground/70 text-right max-w-[200px] truncate">
                    {agentMap[selected].current_task}
                  </span>
                </div>
              )}
              {agentMap[selected].last_heartbeat && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Heartbeat</span>
                  <span className="text-xs text-muted-foreground">
                    {agentMap[selected].last_heartbeat}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Logs / thinking */}
          <div className="flex-1 overflow-auto p-4">
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Activity Log
            </h4>
            {logsLoading ? (
              <p className="text-xs text-muted-foreground">Loading...</p>
            ) : logs.length === 0 ? (
              <p className="text-xs text-muted-foreground">No recent activity</p>
            ) : (
              <div className="space-y-3">
                {logs.map((log) => (
                  <div key={log.id} className="text-xs">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span
                        className={cn(
                          "font-medium",
                          log.role === "assistant"
                            ? "text-blue-400"
                            : log.role === "tool"
                              ? "text-purple-400"
                              : "text-muted-foreground",
                        )}
                      >
                        {log.role}
                      </span>
                      {log.created_at && (
                        <span className="text-muted-foreground/50">
                          {new Date(log.created_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                    <p className="text-foreground/60 whitespace-pre-wrap break-words leading-relaxed">
                      {log.content.length > 500
                        ? log.content.slice(0, 500) + "..."
                        : log.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

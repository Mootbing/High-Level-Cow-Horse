"use client";

import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ExternalLink, GitCommit, Rocket, AlertCircle, RotateCcw } from "lucide-react";

interface Deployment {
  id: string;
  url: string | null;
  state: string;
  created: number | null;
  inspectorUrl: string;
}

interface Commit {
  sha: string;
  short_sha: string;
  message: string;
  author: string;
  date: string;
  url: string;
  branch: string;
  parents: string[];
  deployment: Deployment | null;
}

interface GitTreeProps {
  commits: Commit[];
  branches: string[];
  projectId?: string;
}

const BRANCH_COLORS = [
  "var(--accent)",
  "#34C759",
  "#ff9f0a",
  "#E879A8",
  "#60A5FA",
  "#8e8e93",
];

function formatTime(dateStr: string) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function GitTree({ commits, branches, projectId }: GitTreeProps) {
  const [rollingBackId, setRollingBackId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Find the most recent READY deployment — that's the current prod
  const prodDeploymentId = useMemo(() => {
    const readyCommits = commits.filter(
      (c) => c.deployment?.state === "READY" && c.deployment?.created
    );
    if (readyCommits.length === 0) return null;
    readyCommits.sort(
      (a, b) => (b.deployment!.created || 0) - (a.deployment!.created || 0)
    );
    return readyCommits[0].deployment!.id;
  }, [commits]);

  async function handleRollback(deploymentId: string) {
    if (!projectId || !confirm("Roll back production to this deployment?")) return;
    setRollingBackId(deploymentId);
    try {
      await api.rollbackDeployment(projectId, deploymentId);
      queryClient.invalidateQueries({ queryKey: ["project-history"] });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Rollback failed");
    } finally {
      setRollingBackId(null);
    }
  }

  const branchColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    // main always gets first color
    const sorted = ["main", ...branches.filter((b) => b !== "main")];
    sorted.forEach((b, i) => {
      map[b] = BRANCH_COLORS[i % BRANCH_COLORS.length];
    });
    return map;
  }, [branches]);

  // Assign lane (x position) to each branch
  const branchLanes = useMemo(() => {
    const lanes: Record<string, number> = { main: 0 };
    let nextLane = 1;
    branches.filter((b) => b !== "main").forEach((b) => {
      lanes[b] = nextLane++;
    });
    return lanes;
  }, [branches]);

  const maxLane = Math.max(0, ...Object.values(branchLanes));
  const laneWidth = 24;
  const graphWidth = (maxLane + 1) * laneWidth + 16;

  if (commits.length === 0) {
    return (
      <div className="p-10 text-center text-sm" style={{ color: "var(--text-light)" }}>
        No history yet
      </div>
    );
  }

  // Build a SHA → index map for drawing connections
  const shaIndex = new Map<string, number>();
  commits.forEach((c, i) => shaIndex.set(c.sha, i));

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[500px]">
        {commits.map((commit, i) => {
          const lane = branchLanes[commit.branch] ?? 0;
          const color = branchColorMap[commit.branch] || "var(--text-light)";
          const cx = lane * laneWidth + 16;
          const hasDeployment = commit.deployment !== null;
          const deployReady = commit.deployment?.state === "READY";
          const deployError = commit.deployment?.state === "ERROR";

          // Check if next commit is on a different branch (for drawing merge/branch lines)
          const nextCommit = i < commits.length - 1 ? commits[i + 1] : null;
          const prevCommit = i > 0 ? commits[i - 1] : null;
          const branchChanges = nextCommit && nextCommit.branch !== commit.branch;

          return (
            <div
              key={commit.sha}
              className="flex items-stretch group transition-colors duration-150 hover:bg-[var(--bg-alt)]"
              style={{ borderBottom: "1px solid var(--border)", minHeight: 52 }}
            >
              {/* Graph column */}
              <div className="relative flex-shrink-0" style={{ width: graphWidth }}>
                {/* Vertical line above */}
                {i > 0 && (
                  <div
                    className="absolute top-0"
                    style={{
                      left: cx - 1,
                      width: 2,
                      height: "50%",
                      backgroundColor: color,
                      opacity: 0.4,
                    }}
                  />
                )}
                {/* Vertical line below */}
                {i < commits.length - 1 && (
                  <div
                    className="absolute bottom-0"
                    style={{
                      left: cx - 1,
                      width: 2,
                      height: "50%",
                      backgroundColor: color,
                      opacity: 0.4,
                    }}
                  />
                )}
                {/* Branch/merge line to main */}
                {lane > 0 && (
                  <div
                    className="absolute"
                    style={{
                      left: 15,
                      top: 0,
                      width: 2,
                      height: "100%",
                      backgroundColor: branchColorMap["main"] || "var(--accent)",
                      opacity: 0.15,
                    }}
                  />
                )}
                {/* Horizontal connector for branch commits */}
                {lane > 0 && (i === 0 || prevCommit?.branch !== commit.branch) && (
                  <div
                    className="absolute"
                    style={{
                      left: 16,
                      top: "50%",
                      width: cx - 16,
                      height: 2,
                      backgroundColor: color,
                      opacity: 0.4,
                    }}
                  />
                )}
                {/* Node */}
                <div
                  className="absolute rounded-full"
                  style={{
                    left: cx - (hasDeployment ? 6 : 4),
                    top: "50%",
                    transform: "translateY(-50%)",
                    width: hasDeployment ? 12 : 8,
                    height: hasDeployment ? 12 : 8,
                    backgroundColor: deployError ? "#ef4444" : deployReady ? "#34C759" : color,
                    border: hasDeployment ? "2px solid white" : "none",
                    boxShadow: hasDeployment ? `0 0 0 2px ${deployReady ? "#34C75940" : deployError ? "#ef444440" : color + "40"}` : "none",
                    zIndex: 2,
                  }}
                />
              </div>

              {/* Content */}
              <div className="flex-1 flex items-center gap-3 py-2.5 pr-4 min-w-0">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <a
                      href={commit.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium truncate hover:text-[var(--accent)] transition-colors"
                      style={{ color: "var(--text)" }}
                    >
                      {commit.message}
                    </a>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-data"
                      style={{ backgroundColor: color + "18", color }}
                    >
                      {commit.branch}
                    </span>
                    <span className="text-[10px] font-data" style={{ color: "var(--text-light)" }}>
                      {commit.short_sha}
                    </span>
                    {commit.author && (
                      <span className="text-[10px]" style={{ color: "var(--text-light)" }}>
                        {commit.author}
                      </span>
                    )}
                    <span className="text-[10px]" style={{ color: "var(--text-light)" }}>
                      {formatTime(commit.date)}
                    </span>
                  </div>
                </div>

                {/* Deployment badge */}
                {commit.deployment && (() => {
                  const isProd = commit.deployment.id === prodDeploymentId;
                  return (
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {deployReady && isProd && (
                        <span
                          className="flex items-center gap-1 text-[10px] px-2.5 py-1 rounded-full font-bold"
                          style={{
                            backgroundColor: "#34C759",
                            color: "white",
                          }}
                        >
                          <Rocket size={10} />
                          Prod
                        </span>
                      )}
                      {deployReady && !isProd && projectId && (
                        <button
                          onClick={() => handleRollback(commit.deployment!.id)}
                          disabled={rollingBackId === commit.deployment!.id}
                          className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-full font-medium transition-all duration-200 hover:shadow-sm"
                          style={{
                            backgroundColor: "var(--accent-soft)",
                            color: "var(--accent)",
                            border: "1px solid var(--accent)",
                            opacity: rollingBackId === commit.deployment!.id ? 0.6 : 1,
                          }}
                        >
                          <RotateCcw size={9} className={rollingBackId === commit.deployment!.id ? "animate-spin" : ""} />
                          {rollingBackId === commit.deployment!.id ? "Rolling back..." : "Rollback"}
                        </button>
                      )}
                      {deployReady && commit.deployment.url && (
                        <a
                          href={commit.deployment.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 rounded hover:bg-[var(--bg-alt)] transition-colors"
                          title="Preview URL"
                        >
                          <ExternalLink size={10} style={{ color: "var(--text-light)" }} />
                        </a>
                      )}
                      {deployError && (
                        <span
                          className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-full font-medium"
                          style={{
                            backgroundColor: "#ef444418",
                            color: "#ef4444",
                            border: "1px solid #ef444430",
                          }}
                        >
                          <AlertCircle size={10} />
                          Failed
                        </span>
                      )}
                      <a
                        href={commit.deployment.inspectorUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 rounded hover:bg-[var(--bg-alt)] transition-colors"
                        title="View in Vercel"
                      >
                        <svg width="12" height="12" viewBox="0 0 76 65" fill="var(--text-light)"><path d="M37.5274 0L75.0548 65H0L37.5274 0Z" /></svg>
                      </a>
                    </div>
                  );
                })()}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

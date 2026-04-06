"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/data/status-badge";
import { SortableHeader } from "@/components/data/sortable-header";
import { formatDate } from "@/lib/utils";
import type { Task } from "@/lib/types";
import { RotateCcw, Trash2 } from "lucide-react";

interface TaskTableProps {
  tasks: Task[];
  sort: string;
  onSort: (sort: string) => void;
  /** Hide the Project column (for project-scoped view) */
  compact?: boolean;
}

export function TaskTable({ tasks, sort, onSort, compact }: TaskTableProps) {
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handleRetry(id: string) {
    if (!confirm("Retry this task?")) return;
    setRetryingId(id);
    try {
      await api.retryTask(id);
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["project-tasks"] });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setRetryingId(null);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this task?")) return;
    try {
      await api.deleteTask(id);
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["project-tasks"] });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  }

  const columns = [
    { label: "Title", key: "title" },
    ...(!compact ? [{ label: "Project", key: null as string | null }] : []),
    { label: "Agent", key: "agent_type" },
    { label: "Status", key: "status" },
    { label: "Retries", key: "retry_count" },
    { label: "Started", key: "started_at" },
    { label: "Completed", key: "completed_at" },
  ];

  if (tasks.length === 0) {
    return (
      <div className="p-10 text-center text-sm" style={{ color: "var(--text-light)" }}>
        No tasks yet
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            {columns.map((col) => (
              <SortableHeader key={col.label} label={col.label} sortKey={col.key} currentSort={sort} onSort={onSort} />
            ))}
            <th className="px-3 py-3.5 w-16" />
          </tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.id} className="hover:bg-[var(--bg-alt)] transition-colors" style={{ borderBottom: "1px solid var(--border)" }}>
              <td className="px-5 py-3.5 font-medium" style={{ color: "var(--text)" }}>{t.title}</td>
              {!compact && (
                <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-muted)" }}>{t.project_name || "—"}</td>
              )}
              <td className="px-5 py-3.5">
                <span className="text-xs px-2.5 py-1 rounded-full font-data" style={{ backgroundColor: "var(--bg-alt)", color: "var(--text-muted)" }}>{t.agent_type}</span>
              </td>
              <td className="px-5 py-3.5"><StatusBadge status={t.status} /></td>
              <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text-muted)" }}>{t.retry_count}</td>
              <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(t.started_at)}</td>
              <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(t.completed_at)}</td>
              <td className="px-3 py-3.5">
                {t.status !== "in_progress" && (
                  <div className="flex items-center gap-1">
                    {(t.status === "failed" || t.status === "completed") && (
                      <button
                        onClick={() => handleRetry(t.id)}
                        disabled={retryingId === t.id}
                        className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-200 hover:shadow-sm"
                        style={{
                          backgroundColor: "var(--accent-soft)",
                          color: "var(--accent)",
                          border: "1px solid var(--accent)",
                          opacity: retryingId === t.id ? 0.6 : 1,
                        }}
                        title="Retry task"
                      >
                        <RotateCcw size={11} className={retryingId === t.id ? "animate-spin" : ""} />
                        {retryingId === t.id ? "Queuing..." : "Retry"}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(t.id)}
                      className="p-1.5 rounded-full hover:bg-red-50 transition-colors"
                      title="Delete task"
                    >
                      <Trash2 size={13} className="text-red-400" />
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

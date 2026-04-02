"use client";

import { StatusBadge } from "@/components/data/status-badge";
import { SortableHeader } from "@/components/data/sortable-header";
import { formatDate } from "@/lib/utils";
import type { Task } from "@/lib/types";

interface TaskTableProps {
  tasks: Task[];
  sort: string;
  onSort: (sort: string) => void;
  /** Hide the Project column (for project-scoped view) */
  compact?: boolean;
}

export function TaskTable({ tasks, sort, onSort, compact }: TaskTableProps) {
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

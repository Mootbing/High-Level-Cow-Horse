"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useProject, useProjectTasks, useProjectDeployments } from "@/lib/hooks/use-api";
import { StatusBadge } from "@/components/data/status-badge";
import { formatDate, timeAgo } from "@/lib/utils";
import {
  ArrowLeft,
  ExternalLink,
  GitBranch,
  Clock,
  ListTodo,
  FileCode,
  Rocket,
} from "lucide-react";

const TABS = ["Overview", "Tasks", "Deployments"] as const;
type Tab = (typeof TABS)[number];

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: project, isLoading } = useProject(id);
  const { data: tasks } = useProjectTasks(id);
  const { data: deployments } = useProjectDeployments(id);
  const [tab, setTab] = useState<Tab>("Overview");

  if (isLoading || !project) {
    return (
      <div className="space-y-4 animate-in">
        <div className="skeleton h-8 w-48" />
        <div className="card-static">
          <div className="skeleton h-6 w-64 mb-4" />
          <div className="skeleton h-4 w-full mb-2" />
          <div className="skeleton h-4 w-3/4" />
        </div>
      </div>
    );
  }

  const githubUrl = (project.metadata_ as Record<string, string>)?.github_url;

  return (
    <div className="space-y-5 animate-in max-w-4xl">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Link href="/projects" className="p-2 rounded-full hover:bg-[var(--bg-alt)] transition-colors mt-0.5">
          <ArrowLeft size={18} style={{ color: "var(--text-muted)" }} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-2xl tracking-tight" style={{ fontFamily: "var(--font-serif)", color: "var(--text)", letterSpacing: "-0.02em" }}>
              {project.name}
            </h2>
            <StatusBadge status={project.status} />
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: "var(--text-light)" }}>
            {project.prospect_company && <span>{project.prospect_company}</span>}
            <span className="flex items-center gap-1">
              <Clock size={10} /> Updated {timeAgo(project.updated_at)}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {githubUrl && (
            <a href={githubUrl} target="_blank" rel="noopener noreferrer" className="btn-outline flex items-center gap-1.5 text-xs" title="GitHub">
              <GitBranch size={14} /> Repo
            </a>
          )}
          {project.deployed_url && (
            <a href={project.deployed_url} target="_blank" rel="noopener noreferrer" className="btn-gradient flex items-center gap-1.5 text-xs">
              <ExternalLink size={12} /> View Site
            </a>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-full border" style={{ borderColor: "var(--border)", width: "fit-content" }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
              tab === t ? "bg-[var(--text)] text-[var(--bg)]" : "hover:bg-[var(--bg-alt)]"
            }`}
            style={tab !== t ? { color: "var(--text-muted)" } : {}}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "Overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card-static space-y-3">
            <h3 className="text-label">Details</h3>
            {project.brief && (
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>{project.brief}</p>
            )}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <span className="text-xs" style={{ color: "var(--text-light)" }}>Priority</span>
                <p className="display-number text-xl mt-0.5" style={{ color: "var(--text)" }}>{project.priority}</p>
              </div>
              <div>
                <span className="text-xs" style={{ color: "var(--text-light)" }}>Slug</span>
                <p className="text-sm font-data mt-0.5" style={{ color: "var(--text-muted)" }}>{project.slug}</p>
              </div>
              {project.client_phone && (
                <div>
                  <span className="text-xs" style={{ color: "var(--text-light)" }}>Client Phone</span>
                  <p className="text-sm font-data mt-0.5" style={{ color: "var(--text)" }}>{project.client_phone}</p>
                </div>
              )}
              <div>
                <span className="text-xs" style={{ color: "var(--text-light)" }}>Created</span>
                <p className="text-sm font-data mt-0.5" style={{ color: "var(--text-muted)" }}>{formatDate(project.created_at)}</p>
              </div>
            </div>
          </div>

          <div className="card-static space-y-3">
            <h3 className="text-label">Quick Stats</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { icon: ListTodo, value: project.task_count, label: "Tasks", color: "var(--accent)" },
                { icon: FileCode, value: project.asset_count, label: "Assets", color: "#7C5CFC" },
                { icon: Rocket, value: deployments?.length || 0, label: "Deploys", color: "var(--status-deployed)" },
              ].map((stat) => (
                <div key={stat.label} className="card-inset flex items-center gap-3">
                  <stat.icon size={16} style={{ color: stat.color }} />
                  <div>
                    <p className="display-number text-xl" style={{ color: "var(--text)" }}>{stat.value}</p>
                    <span className="text-[10px] uppercase tracking-wider" style={{ color: "var(--text-light)" }}>{stat.label}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "Tasks" && (
        <div className="card-static p-0 overflow-hidden">
          {tasks && tasks.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Title", "Agent", "Status", "Retries", "Started", "Completed"].map((h) => (
                    <th key={h} className="px-5 py-3.5 text-left text-[11px] font-medium tracking-wider uppercase" style={{ color: "var(--text-light)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id} className="hover:bg-[var(--bg-alt)] transition-colors" style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="px-5 py-3.5 font-medium" style={{ color: "var(--text)" }}>{t.title}</td>
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
          ) : (
            <div className="p-10 text-center text-sm" style={{ color: "var(--text-light)" }}>No tasks yet</div>
          )}
        </div>
      )}

      {tab === "Deployments" && (
        <div className="card-static p-0 overflow-hidden">
          {deployments && deployments.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["URL", "Status", "Deployed"].map((h) => (
                    <th key={h} className="px-5 py-3.5 text-left text-[11px] font-medium tracking-wider uppercase" style={{ color: "var(--text-light)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {deployments.map((d) => (
                  <tr key={d.id} className="hover:bg-[var(--bg-alt)] transition-colors" style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="px-5 py-3.5">
                      {d.url ? (
                        <a href={d.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-[var(--accent)] hover:underline font-data">
                          {d.url} <ExternalLink size={10} />
                        </a>
                      ) : <span className="text-xs" style={{ color: "var(--text-light)" }}>—</span>}
                    </td>
                    <td className="px-5 py-3.5"><StatusBadge status={d.status} /></td>
                    <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(d.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-10 text-center text-sm" style={{ color: "var(--text-light)" }}>No deployments yet</div>
          )}
        </div>
      )}
    </div>
  );
}

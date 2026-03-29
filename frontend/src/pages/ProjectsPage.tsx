import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectSummary } from "../types";
import StatusBadge from "../components/StatusBadge";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.projects(filter || undefined).then(setProjects).catch(() => {});
  }, [filter]);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold">Projects</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
        >
          <option value="">All</option>
          <option value="intake">Intake</option>
          <option value="design">Design</option>
          <option value="build">Build</option>
          <option value="qa">QA</option>
          <option value="deployed">Deployed</option>
        </select>
      </div>

      {projects.length === 0 ? (
        <p className="text-white/40">No projects yet. Use Chat to create one.</p>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="block bg-white/5 border border-white/5 rounded-lg p-4 hover:bg-white/[0.07] transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium">{p.name}</span>
                  <span className="text-white/30 text-sm ml-2">{p.slug}</span>
                </div>
                <StatusBadge status={p.status} />
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
                <span>
                  Tasks: {p.completed_task_count}/{p.task_count}
                </span>
                {p.deployed_url && (
                  <a
                    href={p.deployed_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-500 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {p.deployed_url}
                  </a>
                )}
                {p.created_at && (
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

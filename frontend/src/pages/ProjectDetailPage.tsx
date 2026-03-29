import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectDetail } from "../types";
import StatusBadge from "../components/StatusBadge";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);

  useEffect(() => {
    if (id) api.project(id).then(setProject).catch(() => {});
  }, [id]);

  if (!project) {
    return <div className="p-8 text-white/40">Loading...</div>;
  }

  return (
    <div className="p-8">
      <Link to="/projects" className="text-sm text-white/40 hover:text-white/60 mb-4 inline-block">
        &larr; Back to projects
      </Link>

      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-xl font-bold">{project.name}</h2>
        <StatusBadge status={project.status} />
      </div>

      {project.brief && (
        <p className="text-white/60 mb-6 max-w-2xl">{project.brief}</p>
      )}

      {project.deployed_url && (
        <a
          href={project.deployed_url}
          target="_blank"
          rel="noreferrer"
          className="inline-block mb-6 text-brand-500 hover:underline text-sm"
        >
          {project.deployed_url} &rarr;
        </a>
      )}

      <h3 className="text-lg font-semibold mb-4">
        Tasks ({project.tasks.length})
      </h3>

      {project.tasks.length === 0 ? (
        <p className="text-white/40 text-sm">No tasks yet.</p>
      ) : (
        <div className="space-y-2">
          {project.tasks.map((t) => (
            <div
              key={t.id}
              className="bg-white/5 border border-white/5 rounded-lg p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-0.5 rounded bg-white/10 text-white/60">
                    {t.agent_type}
                  </span>
                  <span className="text-sm">{t.title}</span>
                </div>
                <StatusBadge status={t.status} />
              </div>
              {(t.started_at || t.completed_at) && (
                <div className="flex gap-4 mt-2 text-xs text-white/30">
                  {t.started_at && <span>Started: {new Date(t.started_at).toLocaleString()}</span>}
                  {t.completed_at && <span>Done: {new Date(t.completed_at).toLocaleString()}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

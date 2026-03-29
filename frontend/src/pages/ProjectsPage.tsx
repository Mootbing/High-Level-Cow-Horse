import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectSummary } from "../types";
import StatusBadge from "../components/StatusBadge";
import { Card } from "../components/ui/card";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.projects(filter || undefined).then(setProjects).catch(() => {});
  }, [filter]);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-foreground">Projects</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-card border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
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
        <p className="text-muted-foreground">
          No projects yet. Use Chat to create one.
        </p>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`}>
              <Card className="p-4 hover:bg-accent/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-foreground">
                      {p.name}
                    </span>
                    <span className="text-muted-foreground text-sm ml-2">
                      {p.slug}
                    </span>
                  </div>
                  <StatusBadge status={p.status} />
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span>
                    Tasks: {p.completed_task_count}/{p.task_count}
                  </span>
                  {p.deployed_url && (
                    <a
                      href={p.deployed_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-foreground/60 hover:text-foreground hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {p.deployed_url}
                    </a>
                  )}
                  {p.created_at && (
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

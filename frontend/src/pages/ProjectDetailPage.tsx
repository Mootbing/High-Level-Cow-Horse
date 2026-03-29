import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectDetail } from "../types";
import StatusBadge from "../components/StatusBadge";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ArrowLeft, ExternalLink } from "lucide-react";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);

  useEffect(() => {
    if (id) api.project(id).then(setProject).catch(() => {});
  }, [id]);

  if (!project) {
    return (
      <div className="p-8 text-muted-foreground">Loading...</div>
    );
  }

  return (
    <div className="p-8">
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

      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-xl font-bold text-foreground">{project.name}</h2>
        <StatusBadge status={project.status} />
      </div>

      {project.brief && (
        <p className="text-muted-foreground mb-6 max-w-2xl">{project.brief}</p>
      )}

      {project.deployed_url && (
        <a
          href={project.deployed_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 mb-6 text-foreground/60 hover:text-foreground text-sm hover:underline"
        >
          <ExternalLink className="w-3 h-3" />
          {project.deployed_url}
        </a>
      )}

      <h3 className="text-lg font-semibold mb-4 text-foreground">
        Tasks ({project.tasks.length})
      </h3>

      {project.tasks.length === 0 ? (
        <p className="text-muted-foreground text-sm">No tasks yet.</p>
      ) : (
        <div className="space-y-2">
          {project.tasks.map((t) => (
            <Card key={t.id} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge variant="secondary">{t.agent_type}</Badge>
                  <span className="text-sm text-foreground">{t.title}</span>
                </div>
                <StatusBadge status={t.status} />
              </div>
              {(t.started_at || t.completed_at) && (
                <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                  {t.started_at && (
                    <span>
                      Started: {new Date(t.started_at).toLocaleString()}
                    </span>
                  )}
                  {t.completed_at && (
                    <span>
                      Done: {new Date(t.completed_at).toLocaleString()}
                    </span>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

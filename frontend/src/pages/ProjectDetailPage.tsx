import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ProjectDetail, KanbanBoardResponse } from "../types";
import StatusBadge from "../components/StatusBadge";
import KanbanBoard from "../components/KanbanBoard";
import { Button } from "../components/ui/button";
import { ArrowLeft, ExternalLink, Trash2 } from "lucide-react";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [board, setBoard] = useState<KanbanBoardResponse | null>(null);
  const [deleting, setDeleting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchBoard = useCallback(() => {
    if (id) {
      api.kanbanProject(id).then(setBoard).catch(() => {});
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      api.project(id).then(setProject).catch(() => {});
      fetchBoard();
    }
  }, [id, fetchBoard]);

  // Poll kanban board every 5s
  useEffect(() => {
    pollRef.current = setInterval(fetchBoard, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchBoard]);

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

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-bold text-foreground">{project.name}</h2>
          <StatusBadge status={project.status} />
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
          {deleting ? "Deleting..." : "Delete Project"}
        </Button>
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

      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">
          Task Board
        </h3>
        {board && (
          <span className="text-sm text-muted-foreground">
            {board.total_tasks} tasks
          </span>
        )}
      </div>

      {board ? (
        <KanbanBoard columns={board.columns} />
      ) : (
        <p className="text-muted-foreground text-sm">Loading board...</p>
      )}
    </div>
  );
}

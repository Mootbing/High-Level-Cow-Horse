import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { parseUTC } from "@/lib/utils";
import type { ProjectSummary, KanbanBoardResponse } from "../types";
import StatusBadge from "../components/StatusBadge";
import { Card } from "../components/ui/card";
import { Select } from "../components/ui/select";

function TaskStatusSummary({ projectId }: { projectId: string }) {
  const [board, setBoard] = useState<KanbanBoardResponse | null>(null);

  useEffect(() => {
    api.kanbanProject(projectId).then(setBoard).catch(() => {});
  }, [projectId]);

  if (!board) return null;

  const parts = board.columns
    .filter((col) => col.count > 0)
    .map((col) => `${col.count} ${col.label.toLowerCase()}`);

  if (parts.length === 0) return null;

  return (
    <span className="text-xs text-muted-foreground">
      {parts.join(", ")}
    </span>
  );
}

const PLACEHOLDER_GRADIENTS = [
  "from-violet-600 to-indigo-600",
  "from-cyan-600 to-blue-600",
  "from-emerald-600 to-teal-600",
  "from-orange-600 to-rose-600",
  "from-fuchsia-600 to-pink-600",
  "from-sky-600 to-cyan-600",
];

function hashIndex(str: string, max: number) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return Math.abs(h) % max;
}

function WebsiteThumbnail({ url, name }: { url: string | null; name: string }) {
  const [imgError, setImgError] = useState(false);
  const gradient = PLACEHOLDER_GRADIENTS[hashIndex(name, PLACEHOLDER_GRADIENTS.length)];

  if (!url || imgError) {
    return (
      <div
        className={`w-full h-40 rounded-t-lg bg-gradient-to-br ${gradient} flex items-center justify-center`}
      >
        <span className="text-white/80 text-3xl font-bold uppercase tracking-wider">
          {name.slice(0, 2)}
        </span>
      </div>
    );
  }

  const thumbUrl = `https://image.thum.io/get/width/600/crop/400/${url}`;

  return (
    <div className="w-full h-40 rounded-t-lg overflow-hidden bg-muted">
      <img
        src={thumbUrl}
        alt={`${name} preview`}
        className="w-full h-full object-cover object-top"
        loading="lazy"
        onError={() => setImgError(true)}
      />
    </div>
  );
}

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
        <Select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All</option>
          <option value="intake">Intake</option>
          <option value="design">Design</option>
          <option value="build">Build</option>
          <option value="qa">QA</option>
          <option value="deployed">Deployed</option>
        </Select>
      </div>

      {projects.length === 0 ? (
        <p className="text-muted-foreground">
          No projects yet. Use Chat to create one.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`}>
              <Card className="overflow-hidden hover:bg-accent/50 transition-colors group">
                <WebsiteThumbnail url={p.deployed_url} name={p.name} />
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <span className="font-medium text-foreground truncate block">
                        {p.name}
                      </span>
                      <span className="text-muted-foreground text-sm">
                        {p.slug}
                      </span>
                    </div>
                    <StatusBadge status={p.status} />
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground flex-wrap">
                    <TaskStatusSummary projectId={p.id} />
                    {p.deployed_url && (
                      <a
                        href={p.deployed_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-foreground/60 hover:text-foreground hover:underline truncate max-w-[200px]"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {p.deployed_url.replace(/^https?:\/\//, "")}
                      </a>
                    )}
                    {p.created_at && (
                      <span>{parseUTC(p.created_at)?.toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

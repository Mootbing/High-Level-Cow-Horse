"use client";

import Link from "next/link";
import type { Project } from "@/lib/types";
import { StatusBadge } from "@/components/data/status-badge";
import { timeAgo } from "@/lib/utils";
import { ExternalLink, Mail, ListTodo } from "lucide-react";

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link href={`/projects/${project.id}`} className="block">
      <div className="card cursor-pointer">
        <div className="flex items-start justify-between mb-2">
          <h4
            className="text-sm font-semibold truncate pr-2"
            style={{ color: "var(--text)" }}
          >
            {project.name}
          </h4>
          <StatusBadge status={project.status} />
        </div>

        {project.prospect_company && (
          <p
            className="text-xs mb-2 truncate"
            style={{ color: "var(--text-muted)" }}
          >
            {project.prospect_company}
          </p>
        )}

        <div
          className="flex items-center gap-3 mt-3 text-xs"
          style={{ color: "var(--text-light)" }}
        >
          <span className="flex items-center gap-1">
            <ListTodo size={12} />
            {project.task_count}
          </span>
          <span className="flex items-center gap-1">
            <Mail size={12} />
            {project.email_count}
          </span>
          {project.deployed_url && (
            <span className="flex items-center gap-1 text-[var(--status-deployed)]">
              <ExternalLink size={12} />
              Live
            </span>
          )}
          <span className="ml-auto">{timeAgo(project.updated_at)}</span>
        </div>
      </div>
    </Link>
  );
}

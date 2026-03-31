"use client";

import { useDashboardStats, useProjects } from "@/lib/hooks/use-api";
import { StatCard } from "@/components/cards/stat-card";
import { PipelineChart } from "@/components/charts/pipeline-chart";
import { ProjectCard } from "@/components/cards/project-card";
import {
  Users,
  Rocket,
  Mail,
  Gauge,
  Globe,
  ListTodo,
} from "lucide-react";

export default function OverviewPage() {
  const { data: stats, isLoading } = useDashboardStats();
  const { data: recentProjects } = useProjects({ limit: 6, sort: "-updated_at" });

  if (isLoading || !stats) {
    return (
      <div className="space-y-6 animate-in">
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card-static h-28">
              <div className="skeleton h-4 w-20 mb-3" />
              <div className="skeleton h-8 w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        <StatCard
          label="Prospects"
          value={stats.total_prospects}
          icon={Users}
          color="#7C5CFC"
        />
        <StatCard
          label="Active Projects"
          value={stats.active_projects}
          icon={Rocket}
          color="#60A5FA"
        />
        <StatCard
          label="Deployed"
          value={stats.deployed_projects}
          icon={Globe}
          color="#34C759"
        />
        <StatCard
          label="Emails Sent"
          value={stats.emails_sent}
          icon={Mail}
          color="#ff9f0a"
          subtitle={`${stats.emails_draft} drafts`}
        />
        <StatCard
          label="Tasks Active"
          value={stats.tasks_in_progress}
          icon={ListTodo}
          color="#60A5FA"
          subtitle={`${stats.tasks_completed} completed`}
        />
        <StatCard
          label="Avg Lighthouse"
          value={stats.avg_lighthouse != null ? Math.round(stats.avg_lighthouse) : "—"}
          icon={Gauge}
          color={
            stats.avg_lighthouse != null && stats.avg_lighthouse >= 85
              ? "#34C759"
              : "#E879A8"
          }
        />
      </div>

      {/* Pipeline + Recent Projects */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PipelineChart data={stats.projects_by_status} />

        <div className="card-static">
          <h3 className="text-label mb-5">Recent Projects</h3>
          <div className="space-y-2">
            {recentProjects?.items.length ? (
              recentProjects.items.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))
            ) : (
              <p className="text-sm py-8 text-center" style={{ color: "var(--text-light)" }}>
                No projects yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

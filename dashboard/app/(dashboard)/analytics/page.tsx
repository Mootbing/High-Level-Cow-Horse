"use client";

import { useMetrics, useDashboardStats } from "@/lib/hooks/use-api";
import { MetricsChart } from "@/components/charts/metrics-chart";
import { PipelineChart } from "@/components/charts/pipeline-chart";

export default function AnalyticsPage() {
  const { data: metrics, isLoading } = useMetrics(90);
  const { data: stats } = useDashboardStats();

  const lighthouseData = (metrics || []).map((m) => ({ date: m.metric_date, value: m.avg_lighthouse }));
  const fixLoopsData = (metrics || []).map((m) => ({ date: m.metric_date, value: m.avg_fix_loops }));
  const projectsData = (metrics || []).map((m) => ({ date: m.metric_date, value: m.total_projects }));

  if (isLoading) {
    return (
      <div className="space-y-4 animate-in">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="card-static h-64">
            <div className="skeleton h-4 w-32 mb-4" />
            <div className="skeleton h-48 w-full" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-in">
      {stats && <PipelineChart data={stats.projects_by_status} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MetricsChart data={lighthouseData} label="Avg Lighthouse Score" color="#34C759" />
        <MetricsChart data={fixLoopsData} label="Avg Fix Loops" color="#E879A8" />
      </div>

      <MetricsChart data={projectsData} label="Total Projects Over Time" color="#60A5FA" />
    </div>
  );
}

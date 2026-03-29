import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Overview, AgentsStatusResponse } from "../types";
import { Card, CardContent } from "../components/ui/card";
import { cn } from "@/lib/utils";

function StatCard({
  label,
  value,
  href,
}: {
  label: string;
  value: number | string;
  href?: string;
}) {
  const content = (
    <Card className="hover:bg-accent/50 transition-colors cursor-default">
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-3xl font-bold mt-1 text-foreground">{value}</p>
      </CardContent>
    </Card>
  );
  return href ? <Link to={href}>{content}</Link> : content;
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [agents, setAgents] = useState<AgentsStatusResponse | null>(null);

  useEffect(() => {
    api.overview().then(setOverview).catch(() => {});
    api.agentsStatus().then(setAgents).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-6 text-foreground">Dashboard</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Active Projects"
          value={overview?.active_projects ?? "-"}
          href="/projects"
        />
        <StatCard
          label="Pending Tasks"
          value={overview?.pending_tasks ?? "-"}
        />
        <StatCard
          label="Prospects"
          value={overview?.total_prospects ?? "-"}
          href="/prospects"
        />
        <StatCard
          label="Emails Sent"
          value={overview?.total_emails_sent ?? "-"}
          href="/emails"
        />
      </div>

      <h3 className="text-lg font-semibold mb-4 text-foreground">
        Agent Status
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {agents?.agents.map((a) => (
          <Card key={a.agent_type} className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={cn(
                  "w-2 h-2 rounded-full",
                  a.status === "alive" ? "bg-[#4ade80]" : "bg-[#f87171]"
                )}
              />
              <span className="text-sm font-medium text-foreground">
                {a.agent_type}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {a.tier} &middot; queue: {a.queue_depth}
            </p>
          </Card>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4">
        <StatCard
          label="Total Projects"
          value={overview?.total_projects ?? "-"}
        />
        <StatCard
          label="Completed Tasks"
          value={overview?.completed_tasks ?? "-"}
        />
        <StatCard
          label="Knowledge Entries"
          value={overview?.knowledge_entries ?? "-"}
          href="/knowledge"
        />
        <StatCard
          label="Queue Depth"
          value={agents?.total_pending ?? "-"}
          href="/agents"
        />
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AgentsStatusResponse } from "../types";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { cn } from "@/lib/utils";

export default function AgentsPage() {
  const [data, setData] = useState<AgentsStatusResponse | null>(null);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  function load() {
    api.agentsStatus().then(setData).catch(() => {});
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-foreground">Agents</h2>
        {data && (
          <span className="text-sm text-muted-foreground">
            Total pending: {data.total_pending}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.agents.map((a) => (
          <Card key={a.agent_type}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{a.agent_type}</CardTitle>
                <span
                  className={cn(
                    "w-3 h-3 rounded-full",
                    a.status === "alive" ? "bg-[#4ade80]" : "bg-[#f87171]"
                  )}
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tier</span>
                  <span className="text-foreground/70">{a.tier}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <span
                    className={cn(
                      a.status === "alive"
                        ? "text-[#4ade80]"
                        : "text-[#f87171]"
                    )}
                  >
                    {a.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Queue depth</span>
                  <span
                    className={cn(
                      a.queue_depth > 0
                        ? "text-[#fbbf24]"
                        : "text-foreground/70"
                    )}
                  >
                    {a.queue_depth}
                  </span>
                </div>
                {a.last_heartbeat && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">
                      Last heartbeat
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {a.last_heartbeat}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

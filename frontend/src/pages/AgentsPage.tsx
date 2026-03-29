import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AgentsStatusResponse } from "../types";

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
        <h2 className="text-xl font-bold">Agents</h2>
        {data && (
          <span className="text-sm text-white/40">
            Total pending: {data.total_pending}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.agents.map((a) => (
          <div
            key={a.agent_type}
            className="bg-white/5 border border-white/5 rounded-xl p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">{a.agent_type}</h3>
              <span
                className={`w-3 h-3 rounded-full ${
                  a.status === "alive" ? "bg-green-400" : "bg-red-400"
                }`}
              />
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-white/60">
                <span>Tier</span>
                <span className={a.tier === "heavy" ? "text-orange-300" : "text-blue-300"}>
                  {a.tier}
                </span>
              </div>
              <div className="flex justify-between text-white/60">
                <span>Status</span>
                <span className={a.status === "alive" ? "text-green-300" : "text-red-300"}>
                  {a.status}
                </span>
              </div>
              <div className="flex justify-between text-white/60">
                <span>Queue depth</span>
                <span className={a.queue_depth > 0 ? "text-yellow-300" : ""}>
                  {a.queue_depth}
                </span>
              </div>
              {a.last_heartbeat && (
                <div className="flex justify-between text-white/40">
                  <span>Last heartbeat</span>
                  <span className="text-xs">{a.last_heartbeat}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

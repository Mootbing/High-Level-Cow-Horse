"use client";

import { STATUS_COLORS, STATUS_LABELS, PIPELINE_STAGES } from "@/lib/constants";

interface PipelineChartProps {
  data: Record<string, number>;
}

export function PipelineChart({ data }: PipelineChartProps) {
  const maxVal = Math.max(...Object.values(data), 1);

  return (
    <div className="card-static">
      <h3
        className="text-label mb-5"
      >
        Pipeline
      </h3>
      <div className="space-y-3">
        {PIPELINE_STAGES.map((stage) => {
          const count = data[stage] || 0;
          const pct = (count / maxVal) * 100;
          const color = STATUS_COLORS[stage];
          return (
            <div key={stage} className="flex items-center gap-3">
              <span
                className="text-xs font-medium w-16 text-right"
                style={{ color: "var(--text-muted)" }}
              >
                {STATUS_LABELS[stage]}
              </span>
              <div
                className="flex-1 h-8 rounded-[10px] overflow-hidden"
                style={{ backgroundColor: "var(--bg-alt)" }}
              >
                <div
                  className="h-full rounded-[10px] flex items-center px-3 transition-all duration-700"
                  style={{
                    width: `${Math.max(pct, count > 0 ? 10 : 0)}%`,
                    backgroundColor: `${color}18`,
                    borderLeft: count > 0 ? `3px solid ${color}` : "none",
                  }}
                >
                  {count > 0 && (
                    <span
                      className="text-[12px] font-semibold font-data"
                      style={{ color }}
                    >
                      {count}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

import { Check } from "lucide-react";

const STAGES = [
  { key: "intake", label: "Intake", color: "#60a5fa", icon: "1" },
  { key: "design", label: "Design", color: "#c084fc", icon: "2" },
  { key: "build", label: "Build", color: "#fbbf24", icon: "3" },
  { key: "qa", label: "QA", color: "#fb923c", icon: "4" },
  { key: "deployed", label: "Deployed", color: "#4ade80", icon: "5" },
] as const;

const STAGE_INDEX: Record<string, number> = {};
STAGES.forEach((s, i) => {
  STAGE_INDEX[s.key] = i;
});

export default function ProjectPipelineBar({
  status,
  completedTasks,
  totalTasks,
}: {
  status: string;
  completedTasks: number;
  totalTasks: number;
}) {
  const cancelled = status === "cancelled";
  const activeIdx = STAGE_INDEX[status] ?? -1;
  const isDeployed = status === "deployed";
  const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Overall pipeline progress: each completed stage = 20%, active stage gets partial credit from tasks
  const stageProgress = isDeployed
    ? 100
    : cancelled
      ? 0
      : activeIdx >= 0
        ? (activeIdx / STAGES.length) * 100 + (1 / STAGES.length) * progressPercent
        : 0;

  // Color for the main bar — use the active stage's color
  const barColor = cancelled
    ? "#f87171"
    : isDeployed
      ? "#4ade80"
      : STAGES[activeIdx]?.color ?? "#60a5fa";

  return (
    <div className="w-full mb-8">
      {/* Big progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-muted-foreground">
            Pipeline Progress
          </span>
          <span
            className="text-2xl font-bold tabular-nums"
            style={{ color: barColor }}
          >
            {Math.round(stageProgress)}%
          </span>
        </div>
        <div className="w-full h-4 rounded-full bg-white/5 border border-white/10 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.max(stageProgress, 2)}%`,
              background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
              boxShadow: `0 0 12px ${barColor}50, 0 0 4px ${barColor}40`,
            }}
          />
        </div>
        {totalTasks > 0 && (
          <div className="mt-1.5 text-xs text-muted-foreground">
            {completedTasks} / {totalTasks} tasks completed
          </div>
        )}
      </div>

      {/* Stage indicators */}
      <div className="flex items-center w-full">
        {STAGES.map((stage, i) => {
          const isCompleted = !cancelled && activeIdx > i;
          const isActive = !cancelled && activeIdx === i;

          return (
            <div key={stage.key} className="flex items-center flex-1 last:flex-initial">
              {/* Stage circle + label */}
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className="relative flex items-center justify-center w-9 h-9 rounded-full text-xs font-bold transition-all"
                  style={
                    cancelled
                      ? { background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.2)" }
                      : isCompleted
                        ? { background: stage.color, color: "#000" }
                        : isActive
                          ? {
                              background: `${stage.color}25`,
                              color: stage.color,
                              boxShadow: `0 0 16px ${stage.color}50, 0 0 6px ${stage.color}30`,
                              border: `2px solid ${stage.color}`,
                            }
                          : { background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.2)" }
                  }
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4" strokeWidth={3} />
                  ) : isActive ? (
                    <span
                      className="w-2.5 h-2.5 rounded-full animate-pulse"
                      style={{ background: stage.color }}
                    />
                  ) : (
                    stage.icon
                  )}
                </div>
                <span
                  className="text-xs font-medium whitespace-nowrap"
                  style={{
                    color: cancelled
                      ? "rgba(255,255,255,0.2)"
                      : isCompleted || isActive
                        ? stage.color
                        : "rgba(255,255,255,0.3)",
                  }}
                >
                  {stage.label}
                </span>
              </div>

              {/* Connector line */}
              {i < STAGES.length - 1 && (
                <div
                  className="flex-1 mx-2 h-0.5 min-w-[20px] rounded-full transition-all"
                  style={{
                    background: cancelled
                      ? "rgba(255,255,255,0.06)"
                      : isCompleted
                        ? stage.color
                        : "rgba(255,255,255,0.08)",
                  }}
                />
              )}
            </div>
          );
        })}
      </div>

      {cancelled && (
        <div className="mt-3 text-sm text-[#f87171] font-medium">
          Project cancelled
        </div>
      )}
    </div>
  );
}

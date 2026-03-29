import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { KanbanBoardResponse } from "../types";
import KanbanBoard from "../components/KanbanBoard";
import { useWebSocket } from "../hooks/useWebSocket";

export default function KanbanPage() {
  const [board, setBoard] = useState<KanbanBoardResponse | null>(null);
  const { messages: wsMessages } = useWebSocket();

  useEffect(() => {
    api.kanbanGlobal().then(setBoard).catch(() => {});
  }, []);

  // Auto-refresh when task_update events arrive
  useEffect(() => {
    const taskEvents = wsMessages.filter((m) => m.type === "task_update");
    if (taskEvents.length > 0) {
      api.kanbanGlobal().then(setBoard).catch(() => {});
    }
  }, [wsMessages]);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-foreground">Task Board</h2>
        {board && (
          <span className="text-sm text-muted-foreground">
            {board.total_tasks} tasks
          </span>
        )}
      </div>
      {board ? (
        <KanbanBoard columns={board.columns} />
      ) : (
        <p className="text-muted-foreground">Loading board...</p>
      )}
    </div>
  );
}

# Kanban Board Feature Plan

Replace the unstructured Logs page with a real-time Kanban board that visualizes task flow across all agents. Each project gets its own board (accessible from project detail), plus a global board showing all active work.

---

## 1. Architecture Overview

```
Browser (React)
  |
  |-- GET /api/dashboard/kanban/global         --> all active tasks, grouped by status
  |-- GET /api/dashboard/kanban/project/:id    --> tasks for one project, grouped by status
  |
  |-- WS  /ws/chat (existing)
  |       subscribes to "dashboard:events"
  |       receives: { type: "task_update", task_id, status, agent_type, project_id, ... }
  |       receives: { type: "task_created", task_id, status, agent_type, project_id, ... }
```

Tasks flow automatically through columns based on status changes in the worker pipeline. No drag-and-drop -- cards move when agents update task status via `update_task_status()`.

---

## 2. Kanban Columns

| Column       | Task.status values mapped | Description                          |
|-------------|--------------------------|--------------------------------------|
| Queued      | `pending`                | Task created, waiting for agent      |
| In Progress | `in_progress`            | Agent actively working               |
| Review      | `review`                 | Sent to reviewer agent for QA        |
| Done        | `completed`              | Agent finished successfully          |
| Failed      | `failed`                 | Task errored after max retries       |

Each column header shows `Column Name (count)`.

---

## 3. Card Design

Each card displays:

```
+-----------------------------------------------+
| [engineer]  [in_progress]           2m 14s ago |
|                                                |
| Build homepage layout                          |
|                                                |
| Assigned to: engineer                          |
| Delegated by: project_manager                  |
|                                                |
| [View log entry]                               |
+-----------------------------------------------+
```

**Fields:**
- **Agent badge** -- color-coded by agent type (see color map below)
- **Status badge** -- uses existing StatusBadge component
- **Task title** -- `Task.title`
- **Time elapsed** -- computed from `started_at` (in progress) or `created_at` to `completed_at` (done)
- **Assigned to** -- `Task.agent_type` (which agent is executing)
- **Delegated by** -- `Task.input_data.source_agent` (the agent that created/delegated the task, or derived from `parent_task.agent_type`)
- **View log entry** -- link to the latest `AgentLog` entry associated with this task via `AgentLog.task_id`

**Agent color map** (applied as a left border accent on each card):

| Agent Type        | Color    | Tailwind            |
|-------------------|----------|---------------------|
| ceo               | blue     | `border-l-blue-500` |
| project_manager   | purple   | `border-l-purple-500` |
| inbound           | cyan     | `border-l-cyan-500` |
| outbound          | orange   | `border-l-orange-500` |
| designer          | pink     | `border-l-pink-500` |
| engineer          | green    | `border-l-green-500` |
| qa                | yellow   | `border-l-yellow-500` |
| reviewer          | amber    | `border-l-amber-500` |
| client_comms      | teal     | `border-l-teal-500` |
| research          | indigo   | `border-l-indigo-500` |
| learning          | slate    | `border-l-slate-400` |

---

## 4. New and Modified Files

### Backend (Python)

| File | Action | Purpose |
|------|--------|---------|
| `src/openclaw/schemas/dashboard.py` | MODIFY | Add `KanbanTaskCard` and `KanbanBoardResponse` schemas |
| `src/openclaw/api/dashboard.py` | MODIFY | Add `GET /kanban/global` and `GET /kanban/project/{project_id}` endpoints |
| `src/openclaw/services/task_service.py` | MODIFY | Add `review` status handling in `update_task_status` |
| `src/openclaw/agents/worker.py` | MODIFY | Emit richer `task_update` events with task_id, project_id, title, delegator |
| `src/openclaw/tools/messaging.py` | NO CHANGE | `publish_dashboard_event` already handles arbitrary event dicts |

### Frontend (TypeScript/React)

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/types/index.ts` | MODIFY | Add `KanbanTaskCard`, `KanbanColumn`, `KanbanBoardResponse` types |
| `frontend/src/api/client.ts` | MODIFY | Add `kanbanGlobal()` and `kanbanProject(id)` API methods |
| `frontend/src/pages/LogsPage.tsx` | DELETE | Replaced entirely by KanbanPage |
| `frontend/src/pages/KanbanPage.tsx` | CREATE | Global kanban board (replaces /logs route) |
| `frontend/src/pages/ProjectDetailPage.tsx` | MODIFY | Embed project-scoped kanban board, link to it |
| `frontend/src/components/KanbanBoard.tsx` | CREATE | Reusable board component (columns + cards) |
| `frontend/src/components/KanbanColumn.tsx` | CREATE | Single column with header count and card list |
| `frontend/src/components/KanbanCard.tsx` | CREATE | Individual task card with agent color, times, links |
| `frontend/src/components/Layout.tsx` | MODIFY | Rename "Logs" nav item to "Board", update icon |
| `frontend/src/App.tsx` | MODIFY | Replace `/logs` route with `/board`, import KanbanPage |
| `frontend/src/hooks/useKanbanUpdates.ts` | CREATE | Hook that merges WebSocket `task_update`/`task_created` events into board state |

---

## 5. Backend Changes in Detail

### 5.1 New Pydantic Schemas

Add to `src/openclaw/schemas/dashboard.py`:

```python
class KanbanTaskCard(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    project_name: str | None
    agent_type: str
    title: str
    status: str
    priority: int
    delegated_by: str | None          # source_agent from input_data, or parent_task.agent_type
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    created_at: datetime.datetime | None
    error: str | None
    latest_log_id: uuid.UUID | None   # most recent AgentLog.id for this task

    model_config = {"from_attributes": True}


class KanbanColumn(BaseModel):
    status: str                        # "pending", "in_progress", "review", "completed", "failed"
    label: str                         # "Queued", "In Progress", "Review", "Done", "Failed"
    cards: list[KanbanTaskCard]
    count: int


class KanbanBoardResponse(BaseModel):
    columns: list[KanbanColumn]
    total_tasks: int
```

### 5.2 New API Endpoints

Add to `src/openclaw/api/dashboard.py`:

```python
KANBAN_COLUMNS = [
    ("pending", "Queued"),
    ("in_progress", "In Progress"),
    ("review", "Review"),
    ("completed", "Done"),
    ("failed", "Failed"),
]


@router.get("/kanban/global", response_model=KanbanBoardResponse)
async def kanban_global(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """Global kanban board -- all active tasks across all projects."""
    return await _build_kanban_board(session, project_id=None)


@router.get("/kanban/project/{project_id}", response_model=KanbanBoardResponse)
async def kanban_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """Project-scoped kanban board."""
    return await _build_kanban_board(session, project_id=project_id)
```

### 5.3 Database Query for Populating the Board

```python
async def _build_kanban_board(
    session: AsyncSession,
    project_id: str | None = None,
) -> KanbanBoardResponse:
    """Build the kanban board response from Tasks + AgentLogs."""

    # Base query: tasks with their project name and latest log entry
    base_q = (
        select(
            Task,
            Project.name.label("project_name"),
        )
        .outerjoin(Project, Task.project_id == Project.id)
        .order_by(Task.priority.asc(), Task.created_at.desc())
    )

    if project_id:
        base_q = base_q.where(Task.project_id == project_id)

    result = await session.execute(base_q)
    rows = result.all()

    # Batch-fetch latest log ID per task
    task_ids = [row.Task.id for row in rows]
    latest_logs: dict[uuid.UUID, uuid.UUID] = {}
    if task_ids:
        from sqlalchemy import and_
        log_subq = (
            select(
                AgentLog.task_id,
                func.max(AgentLog.created_at).label("max_created"),
            )
            .where(AgentLog.task_id.in_(task_ids))
            .group_by(AgentLog.task_id)
            .subquery()
        )
        log_q = (
            select(AgentLog.task_id, AgentLog.id)
            .join(
                log_subq,
                and_(
                    AgentLog.task_id == log_subq.c.task_id,
                    AgentLog.created_at == log_subq.c.max_created,
                ),
            )
        )
        log_result = await session.execute(log_q)
        for row in log_result.all():
            latest_logs[row.task_id] = row.id

    # Build columns
    columns = []
    total = 0
    for status, label in KANBAN_COLUMNS:
        cards = []
        for row in rows:
            task = row.Task
            if task.status != status:
                continue
            # Determine delegator: check input_data.source_agent first,
            # fall back to parent_task's agent_type
            delegated_by = task.input_data.get("source_agent") if task.input_data else None
            if not delegated_by and task.parent_task_id:
                parent = await session.get(Task, task.parent_task_id)
                if parent:
                    delegated_by = parent.agent_type

            cards.append(KanbanTaskCard(
                id=task.id,
                project_id=task.project_id,
                project_name=row.project_name,
                agent_type=task.agent_type,
                title=task.title,
                status=task.status,
                priority=task.priority,
                delegated_by=delegated_by,
                started_at=task.started_at,
                completed_at=task.completed_at,
                created_at=task.created_at,
                error=task.error,
                latest_log_id=latest_logs.get(task.id),
            ))
        total += len(cards)
        columns.append(KanbanColumn(
            status=status,
            label=label,
            cards=cards,
            count=len(cards),
        ))

    return KanbanBoardResponse(columns=columns, total_tasks=total)
```

### 5.4 Add "review" Status to Task Service

In `src/openclaw/services/task_service.py`, the `update_task_status` function already handles `in_progress`, `completed`, and `failed`. Add `review`:

```python
# In update_task_status, after the in_progress block:
elif status == "review":
    pass  # No timestamp change, task stays started
```

### 5.5 Richer WebSocket Events from Worker

Currently the worker emits a minimal event. Enrich it to include fields the frontend needs to update cards in place without re-fetching:

```python
# In src/openclaw/agents/worker.py, replace the existing publish_dashboard_event call:
await publish_dashboard_event({
    "type": "task_update",
    "task_id": task_id,
    "agent_type": agent_type,
    "status": "completed",
    "project_id": data.get("project_id"),
    "title": data.get("payload", {}).get("prompt", "")[:100],
    "delegated_by": data.get("source_agent"),
    "entry_id": entry_id,
})
```

Also emit a `task_created` event when tasks are created in `task_service.py`:

```python
# At the end of create_task, after session.refresh(task):
try:
    from openclaw.tools.messaging import publish_dashboard_event
    await publish_dashboard_event({
        "type": "task_created",
        "task_id": str(task.id),
        "agent_type": task.agent_type,
        "status": task.status,
        "project_id": str(task.project_id) if task.project_id else None,
        "title": task.title,
        "delegated_by": (input_data or {}).get("source_agent"),
    })
except Exception:
    pass
```

---

## 6. Frontend Changes in Detail

### 6.1 New TypeScript Types

Add to `frontend/src/types/index.ts`:

```typescript
export interface KanbanTaskCard {
  id: string;
  project_id: string | null;
  project_name: string | null;
  agent_type: string;
  title: string;
  status: string;
  priority: number;
  delegated_by: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
  error: string | null;
  latest_log_id: string | null;
}

export interface KanbanColumn {
  status: string;
  label: string;
  cards: KanbanTaskCard[];
  count: number;
}

export interface KanbanBoardResponse {
  columns: KanbanColumn[];
  total_tasks: number;
}
```

### 6.2 New API Client Methods

Add to `frontend/src/api/client.ts`:

```typescript
kanbanGlobal: () =>
  apiFetch<import("../types").KanbanBoardResponse>("/dashboard/kanban/global"),

kanbanProject: (projectId: string) =>
  apiFetch<import("../types").KanbanBoardResponse>(
    `/dashboard/kanban/project/${projectId}`
  ),
```

### 6.3 `useKanbanUpdates` Hook

`frontend/src/hooks/useKanbanUpdates.ts` -- listens to the existing WebSocket for `task_update` and `task_created` events and patches board state in-memory:

```typescript
import { useEffect } from "react";
import { useWebSocket } from "./useWebSocket";
import type { KanbanBoardResponse, KanbanTaskCard } from "../types";

/**
 * Listens to WebSocket task events and returns a function
 * that applies them to a KanbanBoardResponse state setter.
 */
export function useKanbanUpdates(
  setBoard: React.Dispatch<React.SetStateAction<KanbanBoardResponse | null>>,
  projectFilter?: string,
) {
  const { messages } = useWebSocket();

  useEffect(() => {
    const latest = messages[messages.length - 1];
    if (!latest) return;

    if (latest.type === "task_update" || latest.type === "task_created") {
      // If filtering by project, ignore events for other projects
      const eventProjectId = (latest as any).project_id;
      if (projectFilter && eventProjectId !== projectFilter) return;

      setBoard((prev) => {
        if (!prev) return prev;
        return applyTaskEvent(prev, latest as any);
      });
    }
  }, [messages, setBoard, projectFilter]);
}

function applyTaskEvent(
  board: KanbanBoardResponse,
  event: { task_id: string; status: string; agent_type: string; [k: string]: any },
): KanbanBoardResponse {
  const newColumns = board.columns.map((col) => ({
    ...col,
    // Remove the card from this column if it exists
    cards: col.cards.filter((c) => c.id !== event.task_id),
    count: 0, // recalculate below
  }));

  // Build the updated card
  const existingCard = board.columns
    .flatMap((c) => c.cards)
    .find((c) => c.id === event.task_id);

  const updatedCard: KanbanTaskCard = existingCard
    ? { ...existingCard, status: event.status, agent_type: event.agent_type }
    : {
        id: event.task_id,
        project_id: event.project_id ?? null,
        project_name: null,
        agent_type: event.agent_type,
        title: event.title ?? "New task",
        status: event.status,
        priority: 5,
        delegated_by: event.delegated_by ?? null,
        started_at: null,
        completed_at: null,
        created_at: new Date().toISOString(),
        error: null,
        latest_log_id: null,
      };

  // Insert into the correct column
  const targetCol = newColumns.find((c) => c.status === event.status);
  if (targetCol) {
    targetCol.cards.unshift(updatedCard);
  }

  // Recalculate counts
  let total = 0;
  for (const col of newColumns) {
    col.count = col.cards.length;
    total += col.count;
  }

  return { columns: newColumns, total_tasks: total };
}
```

### 6.4 `KanbanCard` Component

`frontend/src/components/KanbanCard.tsx`:

Uses existing `Card` and `Badge` from shadcn. Left border accent color based on agent type.

```tsx
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import type { KanbanTaskCard } from "../types";
import { Link } from "react-router-dom";
import { Clock, User, GitBranch, FileText } from "lucide-react";

const AGENT_COLORS: Record<string, string> = {
  ceo: "border-l-blue-500",
  project_manager: "border-l-purple-500",
  inbound: "border-l-cyan-500",
  outbound: "border-l-orange-500",
  designer: "border-l-pink-500",
  engineer: "border-l-green-500",
  qa: "border-l-yellow-500",
  reviewer: "border-l-amber-500",
  client_comms: "border-l-teal-500",
  research: "border-l-indigo-500",
  learning: "border-l-slate-400",
};

function timeElapsed(card: KanbanTaskCard): string {
  const start = card.started_at || card.created_at;
  if (!start) return "";
  const end = card.completed_at || new Date().toISOString();
  const diffMs = new Date(end).getTime() - new Date(start).getTime();
  const mins = Math.floor(diffMs / 60000);
  const secs = Math.floor((diffMs % 60000) / 1000);
  if (mins > 60) {
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ${mins % 60}m`;
  }
  return `${mins}m ${secs}s`;
}

export default function KanbanCard({ card }: { card: KanbanTaskCard }) {
  const borderColor = AGENT_COLORS[card.agent_type] || "border-l-gray-500";

  return (
    <Card className={`p-3 border-l-4 ${borderColor} hover:bg-accent/30 transition-colors`}>
      {/* Header row: agent badge + time */}
      <div className="flex items-center justify-between mb-2">
        <Badge variant="secondary" className="text-[10px] font-mono">
          {card.agent_type}
        </Badge>
        <span className="text-[10px] text-muted-foreground flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {timeElapsed(card)}
        </span>
      </div>

      {/* Title */}
      <p className="text-sm font-medium text-foreground mb-2 line-clamp-2">
        {card.title}
      </p>

      {/* Assignment info */}
      <div className="space-y-1 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-1">
          <User className="w-3 h-3" />
          <span>Assigned: {card.agent_type}</span>
        </div>
        {card.delegated_by && (
          <div className="flex items-center gap-1">
            <GitBranch className="w-3 h-3" />
            <span>From: {card.delegated_by}</span>
          </div>
        )}
        {card.project_name && (
          <Link
            to={`/projects/${card.project_id}`}
            className="text-foreground/50 hover:text-foreground hover:underline"
          >
            {card.project_name}
          </Link>
        )}
      </div>

      {/* Error display for failed tasks */}
      {card.error && (
        <p className="mt-2 text-[10px] text-[#f87171] line-clamp-2 font-mono">
          {card.error}
        </p>
      )}

      {/* Link to log entry */}
      {card.latest_log_id && (
        <div className="mt-2 pt-2 border-t border-border">
          <span className="text-[10px] text-foreground/40 flex items-center gap-1 cursor-pointer hover:text-foreground/70">
            <FileText className="w-3 h-3" />
            View agent log
          </span>
        </div>
      )}
    </Card>
  );
}
```

### 6.5 `KanbanColumn` Component

`frontend/src/components/KanbanColumn.tsx`:

```tsx
import type { KanbanColumn as KanbanColumnType } from "../types";
import KanbanCard from "./KanbanCard";

const COLUMN_HEADER_COLORS: Record<string, string> = {
  pending: "text-muted-foreground",
  in_progress: "text-[#fbbf24]",
  review: "text-[#c084fc]",
  completed: "text-[#4ade80]",
  failed: "text-[#f87171]",
};

export default function KanbanColumn({ column }: { column: KanbanColumnType }) {
  const headerColor = COLUMN_HEADER_COLORS[column.status] || "text-foreground";

  return (
    <div className="flex-1 min-w-[260px] max-w-[320px]">
      {/* Column header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <h3 className={`text-sm font-semibold ${headerColor}`}>
          {column.label}
        </h3>
        <span className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">
          {column.count}
        </span>
      </div>

      {/* Cards */}
      <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-1">
        {column.cards.length === 0 ? (
          <p className="text-xs text-muted-foreground/50 text-center py-8">
            No tasks
          </p>
        ) : (
          column.cards.map((card) => (
            <KanbanCard key={card.id} card={card} />
          ))
        )}
      </div>
    </div>
  );
}
```

### 6.6 `KanbanBoard` Component

`frontend/src/components/KanbanBoard.tsx` -- reusable, used in both global and project views:

```tsx
import type { KanbanBoardResponse } from "../types";
import KanbanColumn from "./KanbanColumn";

interface Props {
  board: KanbanBoardResponse | null;
  loading?: boolean;
}

export default function KanbanBoard({ board, loading }: Props) {
  if (loading || !board) {
    return (
      <div className="text-muted-foreground text-sm">Loading board...</div>
    );
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {board.columns.map((col) => (
        <KanbanColumn key={col.status} column={col} />
      ))}
    </div>
  );
}
```

### 6.7 `KanbanPage` (Replaces LogsPage)

`frontend/src/pages/KanbanPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useKanbanUpdates } from "../hooks/useKanbanUpdates";
import type { KanbanBoardResponse } from "../types";
import KanbanBoard from "../components/KanbanBoard";

export default function KanbanPage() {
  const [board, setBoard] = useState<KanbanBoardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.kanbanGlobal()
      .then(setBoard)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Real-time updates via WebSocket
  useKanbanUpdates(setBoard);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">Task Board</h2>
          <p className="text-xs text-muted-foreground mt-1">
            All active tasks across all projects
            {board && ` -- ${board.total_tasks} total`}
          </p>
        </div>
      </div>
      <KanbanBoard board={board} loading={loading} />
    </div>
  );
}
```

### 6.8 Embed Kanban in ProjectDetailPage

Add a project-scoped kanban board to the existing `ProjectDetailPage.tsx`, below the existing task list. Replace the flat task list with the kanban view:

```tsx
// Replace the "Tasks" section in ProjectDetailPage with:
import KanbanBoard from "../components/KanbanBoard";
import { useKanbanUpdates } from "../hooks/useKanbanUpdates";

// Inside the component:
const [board, setBoard] = useState<KanbanBoardResponse | null>(null);

useEffect(() => {
  if (id) {
    api.kanbanProject(id).then(setBoard).catch(() => {});
  }
}, [id]);

useKanbanUpdates(setBoard, id);

// In the JSX, replace the tasks.map section with:
<h3 className="text-lg font-semibold mb-4 text-foreground">
  Task Board
</h3>
<KanbanBoard board={board} />
```

### 6.9 Routing and Navigation Changes

**`frontend/src/App.tsx`:**
- Replace `import LogsPage` with `import KanbanPage`
- Change route from `<Route path="/logs" element={<LogsPage />} />` to `<Route path="/board" element={<KanbanPage />} />`

**`frontend/src/components/Layout.tsx`:**
- Change nav entry from `{ to: "/logs", label: "Logs", icon: ScrollText }` to `{ to: "/board", label: "Board", icon: Columns }` (import `Columns` from lucide-react)

---

## 7. Real-Time Update Flow

```
1. Agent worker picks up task from Redis Stream
   |
2. task_service.update_task_status(session, task_id, "in_progress")
   |
3. Worker calls publish_dashboard_event({
     type: "task_update",
     task_id, status, agent_type, project_id, title, delegated_by
   })
   |
4. Redis PUBLISH to "dashboard:events" channel
   |
5. chat_ws.py relay: _relay_from_redis() reads from pubsub,
   sends JSON over WebSocket to browser
   |
6. useWebSocket hook receives WsMessage, appends to messages[]
   |
7. useKanbanUpdates hook detects task_update/task_created in messages[],
   calls setBoard() with patched state:
   - Removes card from old column
   - Inserts card into new column matching event.status
   - Recalculates column counts
   |
8. React re-renders: card animates to new column via CSS transition
```

No polling. No re-fetch. The board is always live.

---

## 8. Extending WsMessage Type

The existing `WsMessage` type in `frontend/src/types/index.ts` already has optional `agent_type` and `status` fields. Add the kanban-specific fields:

```typescript
export interface WsMessage {
  type: string;
  content?: string;
  media_url?: string;
  agent_type?: string;
  status?: string;
  // Kanban event fields
  task_id?: string;
  project_id?: string;
  title?: string;
  delegated_by?: string;
}
```

---

## 9. CSS/Animation Notes

- Cards entering a column: `animate-in fade-in slide-in-from-top-2` (Tailwind animate plugin, already available via shadcn)
- Cards should have `transition-all duration-300` for smooth state changes
- Columns use `overflow-y-auto` with `max-h-[calc(100vh-200px)]` to scroll independently
- Horizontal scrolling on the board container for smaller screens: `overflow-x-auto`
- Noir theme consistency: all backgrounds use `bg-background`, `bg-card`; text uses `text-foreground`, `text-muted-foreground`

---

## 10. Task Status Lifecycle

Currently tasks use: `pending` -> `in_progress` -> `completed` / `failed`.

This plan adds `review` as a status. When the worker sends a task to the reviewer agent (see `worker.py` line 110-131), it should also update the task status:

```python
# In worker.py, after publishing to reviewer:
if task_id:
    async with async_session_factory() as session:
        await update_task_status(session, task_id, "review")
    await publish_dashboard_event({
        "type": "task_update",
        "task_id": task_id,
        "agent_type": agent_type,
        "status": "review",
        "project_id": data.get("project_id"),
    })
```

Full lifecycle:

```
pending --> in_progress --> review --> completed
                |                        |
                +------> failed <--------+
```

---

## 11. Preserved Access to Raw Logs

The old LogsPage is deleted, but raw log data is still valuable. The kanban card's "View agent log" link opens a slide-over or modal showing the full `AgentLog` entries for that task. This uses the existing `GET /dashboard/agent-logs?task_id=X` endpoint (which needs a small addition to support `task_id` filtering):

```python
# In dashboard.py, modify list_agent_logs:
@router.get("/agent-logs", response_model=list[AgentLogSummary])
async def list_agent_logs(
    agent_type: str | None = None,
    task_id: str | None = None,        # <-- NEW
    limit: int = Query(100, le=500),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    q = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
    if agent_type:
        q = q.where(AgentLog.agent_type == agent_type)
    if task_id:                          # <-- NEW
        q = q.where(AgentLog.task_id == task_id)
    result = await session.execute(q)
    return [AgentLogSummary.model_validate(a) for a in result.scalars().all()]
```

---

## 12. Implementation Order

1. **Backend schemas** -- Add `KanbanTaskCard`, `KanbanColumn`, `KanbanBoardResponse` to `schemas/dashboard.py`
2. **Backend query** -- Add `_build_kanban_board` helper and two endpoints to `api/dashboard.py`
3. **Backend events** -- Enrich `task_update` events in `worker.py`, add `task_created` event in `task_service.py`, add `review` status support
4. **Backend logs filter** -- Add `task_id` parameter to `list_agent_logs`
5. **Frontend types** -- Add kanban types to `types/index.ts`, extend `WsMessage`
6. **Frontend API** -- Add `kanbanGlobal` and `kanbanProject` to `client.ts`
7. **Frontend components** -- Build `KanbanCard`, `KanbanColumn`, `KanbanBoard`
8. **Frontend hook** -- Build `useKanbanUpdates`
9. **Frontend pages** -- Build `KanbanPage`, modify `ProjectDetailPage`
10. **Frontend routing** -- Update `App.tsx` and `Layout.tsx`
11. **Delete** `LogsPage.tsx`

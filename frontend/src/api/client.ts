const BASE = "/api";

let _redirecting = false;

function getToken(): string {
  return localStorage.getItem("openclaw_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("openclaw_token", token);
}

export function clearToken() {
  localStorage.removeItem("openclaw_token");
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem("openclaw_token");
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    if (!_redirecting) {
      _redirecting = true;
      clearToken();
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  login: (password: string) =>
    apiFetch<{ token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  overview: () => apiFetch<import("../types").Overview>("/dashboard/overview"),

  projects: (status?: string) =>
    apiFetch<import("../types").ProjectSummary[]>(
      `/dashboard/projects${status ? `?status=${status}` : ""}`
    ),

  project: (id: string) =>
    apiFetch<import("../types").ProjectDetail>(`/dashboard/projects/${id}`),

  agentsStatus: () =>
    apiFetch<import("../types").AgentsStatusResponse>("/dashboard/agents/status"),

  prospects: () =>
    apiFetch<import("../types").ProspectSummary[]>("/dashboard/prospects"),

  emails: (limit = 50, status?: string) =>
    apiFetch<import("../types").EmailLogSummary[]>(
      `/dashboard/emails?limit=${limit}${status ? `&status=${status}` : ""}`
    ),

  emailDrafts: () =>
    apiFetch<import("../types").EmailLogSummary[]>("/dashboard/emails/drafts"),

  updateEmailDraft: (id: string, data: { subject?: string; body?: string }) =>
    apiFetch<import("../types").EmailLogSummary>(`/dashboard/emails/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  sendEmailDraft: (id: string) =>
    apiFetch<import("../types").EmailLogSummary>(`/dashboard/emails/${id}/send`, {
      method: "POST",
    }),

  discardEmailDraft: (id: string) =>
    apiFetch<{ status: string; id: string }>(`/dashboard/emails/${id}`, {
      method: "DELETE",
    }),

  deleteProject: (id: string) =>
    apiFetch<{ status: string; slug: string }>(`/dashboard/projects/${id}`, {
      method: "DELETE",
    }),

  kanbanGlobal: () =>
    apiFetch<import("../types").KanbanBoardResponse>("/dashboard/kanban/global"),

  kanbanProject: (projectId: string) =>
    apiFetch<import("../types").KanbanBoardResponse>(`/dashboard/kanban/project/${projectId}`),

  agentLogs: (agentType?: string, limit = 100) =>
    apiFetch<import("../types").AgentLogEntry[]>(
      `/dashboard/agent-logs?limit=${limit}${agentType ? `&agent_type=${agentType}` : ""}`
    ),

  agentLogsByProject: (projectId: string, limit = 200) =>
    apiFetch<import("../types").AgentLogEntry[]>(
      `/dashboard/agent-logs?limit=${limit}&project_id=${projectId}`
    ),

  allAgentLogs: (opts: { agentType?: string; projectId?: string; limit?: number } = {}) => {
    const limit = opts.limit ?? 200;
    const params = new URLSearchParams({ limit: String(limit) });
    if (opts.agentType) params.set("agent_type", opts.agentType);
    if (opts.projectId) params.set("project_id", opts.projectId);
    return apiFetch<import("../types").AgentLogEntry[]>(
      `/dashboard/agent-logs?${params.toString()}`
    );
  },

  knowledge: (category?: string) =>
    apiFetch<import("../types").KnowledgeEntry[]>(
      `/dashboard/knowledge${category ? `?category=${category}` : ""}`
    ),

  messages: (limit = 50) =>
    apiFetch<import("../types").ChatMessage[]>(`/dashboard/messages?limit=${limit}`),

  // Queue management
  queues: () =>
    apiFetch<import("../types").QueueInfo[]>("/dashboard/queues"),

  flushQueue: (agentType: string) =>
    apiFetch<{ status: string }>(`/dashboard/queues/${agentType}`, {
      method: "DELETE",
    }),

  flushAllQueues: () =>
    apiFetch<{ status: string }>("/dashboard/queues/all", {
      method: "DELETE",
    }),

  cancelQueueMessage: (agentType: string, entryId: string) =>
    apiFetch<{ status: string; entry_id: string; agent_type: string }>(
      `/dashboard/queues/${agentType}/${entryId}`,
      { method: "DELETE" }
    ),
};

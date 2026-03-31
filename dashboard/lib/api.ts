import type {
  DashboardStats,
  Deployment,
  EmailLog,
  KnowledgeEntry,
  Message,
  Metric,
  PaginatedResponse,
  Project,
  ProjectStats,
  Prospect,
  ProspectGeo,
  Task,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

function qs(params: Record<string, string | number | undefined | null>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (entries.length === 0) return "";
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

// Prospects
export const api = {
  // Dashboard
  getDashboardStats: () => fetchApi<DashboardStats>("/api/v1/metrics/dashboard"),

  // Prospects
  getProspects: (params?: {
    offset?: number;
    limit?: number;
    industry?: string;
    search?: string;
    sort?: string;
  }) =>
    fetchApi<PaginatedResponse<Prospect>>(
      `/api/v1/prospects${qs(params ?? {})}`
    ),

  getProspect: (id: string) => fetchApi<Prospect>(`/api/v1/prospects/${id}`),

  getProspectsGeo: () => fetchApi<ProspectGeo[]>("/api/v1/prospects/geo"),

  // Projects
  getProjects: (params?: {
    offset?: number;
    limit?: number;
    status?: string;
    search?: string;
    sort?: string;
  }) =>
    fetchApi<PaginatedResponse<Project>>(
      `/api/v1/projects${qs(params ?? {})}`
    ),

  getProject: (id: string) => fetchApi<Project>(`/api/v1/projects/${id}`),

  getProjectStats: () => fetchApi<ProjectStats>("/api/v1/projects/stats"),

  getProjectTasks: (id: string) =>
    fetchApi<Task[]>(`/api/v1/projects/${id}/tasks`),

  getProjectDeployments: (id: string) =>
    fetchApi<Deployment[]>(`/api/v1/projects/${id}/deployments`),

  // Tasks
  getTasks: (params?: {
    offset?: number;
    limit?: number;
    status?: string;
    agent_type?: string;
  }) => fetchApi<PaginatedResponse<Task>>(`/api/v1/tasks${qs(params ?? {})}`),

  // Emails
  getEmails: (params?: { offset?: number; limit?: number; status?: string }) =>
    fetchApi<PaginatedResponse<EmailLog>>(
      `/api/v1/emails${qs(params ?? {})}`
    ),

  getEmail: (id: string) => fetchApi<EmailLog>(`/api/v1/emails/${id}`),

  // Messages
  getMessages: (params?: {
    offset?: number;
    limit?: number;
    project_id?: string;
  }) =>
    fetchApi<PaginatedResponse<Message>>(
      `/api/v1/messages${qs(params ?? {})}`
    ),

  // Knowledge
  getKnowledge: (params?: {
    offset?: number;
    limit?: number;
    category?: string;
    search?: string;
  }) =>
    fetchApi<PaginatedResponse<KnowledgeEntry>>(
      `/api/v1/knowledge${qs(params ?? {})}`
    ),

  // Metrics
  getMetrics: (days?: number) =>
    fetchApi<Metric[]>(`/api/v1/metrics${qs({ days })}`),
};

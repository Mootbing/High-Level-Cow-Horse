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

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
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
    prospects_only?: boolean;
  }) =>
    fetchApi<PaginatedResponse<Prospect>>(
      `/api/v1/prospects${qs(params ?? {})}`
    ),

  getProspect: (id: string) => fetchApi<Prospect>(`/api/v1/prospects/${id}`),

  deleteProspect: (id: string) =>
    fetchApi<{ ok: boolean }>(`/api/v1/prospects/${id}`, { method: "DELETE" }),

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
    sort?: string;
  }) => fetchApi<PaginatedResponse<Task>>(`/api/v1/tasks${qs(params ?? {})}`),

  deleteTask: (id: string) =>
    fetchApi<{ ok: boolean }>(`/api/v1/tasks/${id}`, { method: "DELETE" }),

  retryTask: (id: string) =>
    fetchApi<Task>(`/api/v1/tasks/${id}/retry`, { method: "POST" }),

  // Emails
  getEmails: (params?: { offset?: number; limit?: number; status?: string; project_id?: string; sort?: string }) =>
    fetchApi<PaginatedResponse<EmailLog>>(
      `/api/v1/emails${qs(params ?? {})}`
    ),

  getEmail: (id: string) => fetchApi<EmailLog>(`/api/v1/emails/${id}`),

  updateEmail: (id: string, data: { subject?: string; body?: string }) =>
    fetchApi<EmailLog>(`/api/v1/emails/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteEmail: (id: string) =>
    fetchApi<{ ok: boolean }>(`/api/v1/emails/${id}`, { method: "DELETE" }),

  regenerateEmail: (id: string, instructions?: string) =>
    fetchApi<EmailLog>(`/api/v1/emails/${id}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ instructions }),
    }),

  sendEmail: (id: string) =>
    fetchApi<EmailLog>(`/api/v1/emails/${id}/send`, {
      method: "POST",
    }),

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

  rollbackDeployment: (projectId: string, deploymentId: string) =>
    fetchApi<{ ok: boolean }>(`/api/v1/projects/${projectId}/rollback`, {
      method: "POST",
      body: JSON.stringify({ deployment_id: deploymentId }),
    }),

  // History
  getProjectHistory: (id: string) =>
    fetchApi<{
      commits: Array<{
        sha: string;
        short_sha: string;
        message: string;
        author: string;
        date: string;
        url: string;
        branch: string;
        parents: string[];
        deployment: {
          id: string;
          url: string | null;
          state: string;
          created: number | null;
          inspectorUrl: string;
        } | null;
      }>;
      branches: string[];
      deploy_count: number;
    }>(`/api/v1/projects/${id}/history`),

  // Delete
  deleteProject: (id: string) =>
    fetchApi<{ ok: boolean }>(`/api/v1/projects/${id}`, { method: "DELETE" }),
};

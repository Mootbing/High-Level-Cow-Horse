export interface Overview {
  active_projects: number;
  total_projects: number;
  pending_tasks: number;
  completed_tasks: number;
  total_prospects: number;
  total_emails_sent: number;
  knowledge_entries: number;
}

export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  priority: number;
  deployed_url: string | null;
  task_count: number;
  completed_task_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskSummary {
  id: string;
  agent_type: string;
  title: string;
  status: string;
  priority: number;
  parent_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface ProjectDetail extends Omit<ProjectSummary, "task_count" | "completed_task_count"> {
  brief: string | null;
  metadata_: Record<string, unknown>;
  tasks: TaskSummary[];
}

export interface AgentStatus {
  agent_type: string;
  tier: string;
  status: string;
  queue_depth: number;
  last_heartbeat: string | null;
}

export interface AgentsStatusResponse {
  agents: AgentStatus[];
  total_pending: number;
}

export interface ProspectSummary {
  id: string;
  url: string;
  company_name: string | null;
  industry: string | null;
  contact_emails: string[];
  brand_colors: string[];
  tech_stack: string[];
  scraped_at: string | null;
}

export interface EmailLogSummary {
  id: string;
  to_email: string;
  subject: string | null;
  status: string;
  sent_at: string | null;
  prospect_id: string | null;
  project_id: string | null;
}

export interface KnowledgeEntry {
  id: string;
  category: string;
  title: string;
  content: string;
  relevance_score: number;
  tags: string[];
  source_url: string | null;
  created_at: string | null;
}

export interface ChatMessage {
  id: string;
  direction: string;
  content: string | null;
  media_url: string | null;
  created_at: string | null;
}

export interface WsMessage {
  type: string;
  content?: string;
  media_url?: string;
  agent_type?: string;
  status?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface Prospect {
  id: string;
  url: string;
  company_name: string | null;
  tagline: string | null;
  contact_emails: string[];
  brand_colors: string[];
  fonts: string[];
  logo_url: string | null;
  phone_number: string | null;
  social_links: Record<string, string>;
  industry: string | null;
  tech_stack: string[];
  raw_data: Record<string, unknown>;
  latitude: number | null;
  longitude: number | null;
  scraped_at: string | null;
  created_at: string | null;
  project_count: number;
  site_problems_count: number;
}

export interface ProspectGeo {
  id: string;
  company_name: string | null;
  url: string;
  latitude: number;
  longitude: number;
  industry: string | null;
  project_status: string | null;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  client_phone: string | null;
  brief: string | null;
  status: string;
  priority: number;
  prospect_id: string | null;
  metadata_: Record<string, unknown>;
  deployed_url: string | null;
  created_at: string | null;
  updated_at: string | null;
  prospect_company: string | null;
  task_count: number;
  email_count: number;
}

export interface ProjectStats {
  total: number;
  by_status: Record<string, number>;
}

export interface EmailLog {
  id: string;
  prospect_id: string | null;
  project_id: string | null;
  to_email: string;
  subject: string | null;
  body: string | null;
  edited_subject: string | null;
  edited_body: string | null;
  status: string;
  gmail_message_id: string | null;
  created_at: string | null;
  sent_at: string | null;
  prospect_company: string | null;
  project_name: string | null;
}

export interface Task {
  id: string;
  project_id: string | null;
  parent_task_id: string | null;
  agent_type: string;
  title: string;
  description: string | null;
  status: string;
  priority: number;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error: string | null;
  retry_count: number;
  max_retries: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  project_name: string | null;
}

export interface Message {
  id: string;
  project_id: string | null;
  channel: string;
  direction: string;
  external_message_id: string | null;
  phone_number: string;
  message_type: string;
  content: string | null;
  media_url: string | null;
  status: string;
  created_at: string | null;
  project_name: string | null;
}

export interface Asset {
  id: string;
  project_id: string | null;
  task_id: string | null;
  asset_type: string;
  filename: string;
  storage_path: string;
  mime_type: string | null;
  metadata_: Record<string, unknown>;
  created_at: string | null;
}

export interface Deployment {
  id: string;
  project_id: string | null;
  deployment_id: string | null;
  url: string | null;
  status: string;
  created_at: string | null;
}

export interface KnowledgeEntry {
  id: string;
  category: string;
  title: string;
  content: string;
  source_url: string | null;
  tags: string[];
  code_snippet: string | null;
  relevance_score: number;
  project_id: string | null;
  expires_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Metric {
  id: string;
  metric_date: string;
  avg_lighthouse: number | null;
  avg_fix_loops: number | null;
  avg_project_hours: number | null;
  total_projects: number | null;
  knowledge_entries: number | null;
  prompt_version: number | null;
  notes: string | null;
  created_at: string | null;
}

export interface DashboardStats {
  total_prospects: number;
  total_projects: number;
  active_projects: number;
  deployed_projects: number;
  emails_sent: number;
  emails_draft: number;
  tasks_in_progress: number;
  tasks_completed: number;
  avg_lighthouse: number | null;
  projects_by_status: Record<string, number>;
}

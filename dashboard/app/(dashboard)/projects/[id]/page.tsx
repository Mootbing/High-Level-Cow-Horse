"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useProject, useProjectTasks, useProjectDeployments, useProjectEmails, useProspect, useProjectHistory } from "@/lib/hooks/use-api";

const MapView = dynamic(() => import("@/components/map/map-container"), { ssr: false });
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/data/status-badge";
import { GitTree } from "@/components/charts/git-tree";
import { EmailTable } from "@/components/tables/email-table";
import { TaskTable } from "@/components/tables/task-table";
import { formatDate, timeAgo } from "@/lib/utils";
import {
  ArrowLeft,
  ExternalLink,
  GitBranch,
  Clock,
  ListTodo,
  Rocket,
  Trash2,
  Mail,
} from "lucide-react";

const TABS = ["Overview", "Tasks", "Emails", "History"] as const;
type Tab = (typeof TABS)[number];

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: project, isLoading } = useProject(id);
  const { data: tasks } = useProjectTasks(id);
  const { data: deployments } = useProjectDeployments(id);
  const { data: emails } = useProjectEmails(id);
  const { data: prospect } = useProspect(project?.prospect_id || "");
  const { data: history } = useProjectHistory(id);
  const [tab, setTab] = useState<Tab>("Overview");
  const [taskSort, setTaskSort] = useState("-created_at");
  const [emailSort, setEmailSort] = useState("-created_at");
  const router = useRouter();


  async function handleDelete() {
    const confirmed = prompt(
      `Type "${project?.name}" to permanently delete this project:`
    );
    if (confirmed === project?.name) {
      await api.deleteProject(id);
      router.push("/projects");
    }
  }

  if (isLoading || !project) {
    return (
      <div className="space-y-4 animate-in">
        <div className="skeleton h-8 w-48" />
        <div className="card-static">
          <div className="skeleton h-6 w-64 mb-4" />
          <div className="skeleton h-4 w-full mb-2" />
          <div className="skeleton h-4 w-3/4" />
        </div>
      </div>
    );
  }

  const meta = project.metadata_ as Record<string, string>;
  const githubUrl = meta?.github_url;
  const vercelProject = meta?.vercel_project;
  const vercelUrl = vercelProject ? `https://vercel.com/jason-clarmi/${vercelProject}` : null;

  return (
    <div className="space-y-5 animate-in max-w-4xl">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Link href="/projects" className="p-2 rounded-full hover:bg-[var(--bg-alt)] transition-colors mt-0.5">
          <ArrowLeft size={18} style={{ color: "var(--text-muted)" }} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-2xl tracking-tight" style={{ fontFamily: "var(--font-serif)", color: "var(--text)", letterSpacing: "-0.02em" }}>
              {project.name}
            </h2>
            <StatusBadge status={project.status} />
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: "var(--text-light)" }}>
            {project.prospect_company && <span>{project.prospect_company}</span>}
            <span className="flex items-center gap-1">
              <Clock size={10} /> Updated {timeAgo(project.updated_at)}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {githubUrl && (
            <a href={githubUrl} target="_blank" rel="noopener noreferrer" className="btn-outline flex items-center gap-1.5 text-xs" title="GitHub">
              <GitBranch size={14} /> Repo
            </a>
          )}
          {vercelUrl && (
            <a href={vercelUrl} target="_blank" rel="noopener noreferrer" className="btn-outline flex items-center gap-1.5 text-xs" title="Vercel">
              <svg width="14" height="14" viewBox="0 0 76 65" fill="currentColor"><path d="M37.5274 0L75.0548 65H0L37.5274 0Z" /></svg>
              Vercel
            </a>
          )}
          {project.deployed_url && (
            <a href={project.deployed_url} target="_blank" rel="noopener noreferrer" className="btn-gradient flex items-center gap-1.5 text-xs">
              <ExternalLink size={12} /> View Site
            </a>
          )}
          <button
            onClick={handleDelete}
            className="p-2 rounded-full border transition-all duration-300 hover:bg-red-50 hover:border-red-300"
            style={{ borderColor: "var(--border)" }}
            title="Delete project"
          >
            <Trash2 size={14} className="text-red-400 hover:text-red-600 transition-colors" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-full border" style={{ borderColor: "var(--border)", width: "fit-content" }}>
        {TABS.map((t) => {
          const counts: Record<string, number | undefined> = {
            Tasks: project.task_count,
            Emails: emails?.total,
            History: history?.commits.length,
          };
          const count = counts[t];
          const isActive = tab === t;
          return (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
                isActive ? "bg-[var(--text)] text-[var(--bg)]" : "hover:bg-[var(--bg-alt)]"
              }`}
              style={!isActive ? { color: "var(--text-muted)" } : {}}
            >
              {t}
              {count !== undefined && count > 0 && (
                <span
                  className="flex items-center justify-center rounded-full text-[9px] font-semibold"
                  style={{
                    minWidth: 16,
                    height: 16,
                    backgroundColor: isActive ? "var(--bg)" : "var(--bg-alt)",
                    color: isActive ? "var(--text)" : "var(--text-muted)",
                  }}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {tab === "Overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card-static space-y-3">
            <h3 className="text-label">Details</h3>
            {project.brief && (
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>{project.brief}</p>
            )}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <span className="text-xs" style={{ color: "var(--text-light)" }}>Priority</span>
                <p className="text-xl font-bold tracking-tight mt-0.5" style={{ color: "var(--text)" }}>{project.priority}</p>
              </div>
              <div>
                <span className="text-xs" style={{ color: "var(--text-light)" }}>Slug</span>
                <p className="text-sm font-data mt-0.5" style={{ color: "var(--text-muted)" }}>{project.slug}</p>
              </div>
              {project.client_phone && (
                <div>
                  <span className="text-xs" style={{ color: "var(--text-light)" }}>Client Phone</span>
                  <p className="text-sm font-data mt-0.5" style={{ color: "var(--text)" }}>{project.client_phone}</p>
                </div>
              )}
              <div>
                <span className="text-xs" style={{ color: "var(--text-light)" }}>Created</span>
                <p className="text-sm font-data mt-0.5" style={{ color: "var(--text-muted)" }}>{formatDate(project.created_at)}</p>
              </div>
            </div>
          </div>

          <div className="card-static space-y-1">
            <h3 className="text-label mb-2">Quick Stats</h3>
            {[
              { icon: ListTodo, value: project.task_count, label: "Tasks", color: "var(--accent)" },
              { icon: Mail, value: emails?.total || 0, label: "Emails", color: "#ff9f0a" },
              { icon: Rocket, value: history?.deploy_count ?? 0, label: "Deploys", color: "var(--status-deployed)" },
            ].map((stat) => (
              <div key={stat.label} className="flex items-center gap-3 py-2" style={{ borderBottom: "1px solid var(--border)" }}>
                <stat.icon size={14} style={{ color: stat.color }} />
                <span className="text-sm flex-1" style={{ color: "var(--text-muted)" }}>{stat.label}</span>
                <span className="text-sm font-bold" style={{ color: "var(--text)" }}>{stat.value}</span>
              </div>
            ))}
          </div>
          {prospect?.latitude && prospect?.longitude && (
            <div className="card-static space-y-3 md:col-span-2">
              <h3 className="text-label">Location</h3>
              <div className="rounded-xl overflow-hidden" style={{ height: 220 }}>
                <MapView
                  prospects={[{
                    id: prospect.id,
                    company_name: prospect.company_name,
                    url: prospect.url,
                    latitude: prospect.latitude,
                    longitude: prospect.longitude,
                    industry: prospect.industry,
                    project_status: project.status,
                  }]}
                  isLoading={false}
                />
              </div>
            </div>
          )}

          {/* Prospect section */}
          {prospect && (
            <>
              <h3 className="text-label md:col-span-2 mt-2">Prospect</h3>

              <div className="card-static md:col-span-2">
                <h4 className="text-label mb-2">Original Website</h4>
                <a href={prospect.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-sm text-[var(--accent)] hover:underline font-data">
                  {prospect.url} <ExternalLink size={11} />
                </a>
              </div>

              <div className="card-static space-y-4">
                <h4 className="text-label">Brand Identity</h4>
                {prospect.tagline && (
                  <p className="text-sm italic" style={{ color: "var(--text-muted)", fontFamily: "var(--font-serif)" }}>
                    &ldquo;{prospect.tagline}&rdquo;
                  </p>
                )}
                {prospect.brand_colors.length > 0 && (
                  <div>
                    <span className="text-xs" style={{ color: "var(--text-light)" }}>Colors</span>
                    <div className="flex gap-2.5 mt-1.5">
                      {prospect.brand_colors.map((c, i) => (
                        <div key={i} className="flex flex-col items-center gap-1">
                          <span className="w-8 h-8 rounded-lg border" style={{ backgroundColor: c, borderColor: "var(--border)" }} />
                          <span className="text-[10px] font-data" style={{ color: "var(--text-light)" }}>{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {prospect.fonts.length > 0 && (
                  <div>
                    <span className="text-xs" style={{ color: "var(--text-light)" }}>Fonts</span>
                    <div className="flex gap-1.5 mt-1 flex-wrap">
                      {prospect.fonts.map((f, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded-full" style={{ backgroundColor: "var(--bg-alt)", color: "var(--text-muted)" }}>{f}</span>
                      ))}
                    </div>
                  </div>
                )}
                {prospect.industry && (
                  <div>
                    <span className="text-xs" style={{ color: "var(--text-light)" }}>Industry</span>
                    <p className="text-sm mt-0.5" style={{ color: "var(--text)" }}>{prospect.industry}</p>
                  </div>
                )}
              </div>

              <div className="card-static space-y-4">
                <h4 className="text-label">Contact & Tech</h4>
                {prospect.contact_emails.length > 0 && (
                  <div>
                    <span className="text-xs" style={{ color: "var(--text-light)" }}>Emails</span>
                    <div className="space-y-0.5 mt-1">
                      {prospect.contact_emails.map((e, i) => (
                        <p key={i} className="text-sm font-data" style={{ color: "var(--text)" }}>{e}</p>
                      ))}
                    </div>
                  </div>
                )}
                {prospect.tech_stack.length > 0 && (
                  <div>
                    <span className="text-xs" style={{ color: "var(--text-light)" }}>Tech Stack</span>
                    <div className="flex gap-1.5 mt-1 flex-wrap">
                      {prospect.tech_stack.map((t, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded-full font-data" style={{ backgroundColor: "var(--accent-soft)", color: "var(--accent)" }}>{t}</span>
                      ))}
                    </div>
                  </div>
                )}
                {Object.keys(prospect.social_links).length > 0 && (
                  <div>
                    <span className="text-xs" style={{ color: "var(--text-light)" }}>Social</span>
                    <div className="space-y-1 mt-1">
                      {Object.entries(prospect.social_links).map(([platform, url]) => (
                        <a key={platform} href={url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-xs text-[var(--accent)] hover:underline">
                          {platform} <ExternalLink size={9} />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
                <div>
                  <span className="text-xs" style={{ color: "var(--text-light)" }}>Scraped</span>
                  <p className="text-sm font-data mt-0.5" style={{ color: "var(--text-muted)" }}>{formatDate(prospect.scraped_at)}</p>
                </div>
              </div>

              {(() => {
                const problems = (prospect.raw_data?.site_problems as string[]) || [];
                return problems.length > 0 ? (
                  <div className="card-static md:col-span-2">
                    <h4 className="text-label mb-3">Site Problems ({problems.length})</h4>
                    <ul className="space-y-2">
                      {problems.map((problem, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm" style={{ color: "var(--text-muted)" }}>
                          <span className="mt-2 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: "var(--status-qa)" }} />
                          {problem}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null;
              })()}
            </>
          )}
        </div>
      )}

      {tab === "Tasks" && (
        <div className="card-static p-0 overflow-hidden">
          <TaskTable tasks={tasks || []} sort={taskSort} onSort={setTaskSort} compact />
        </div>
      )}

      {tab === "Emails" && (
        <div className="card-static p-0 overflow-hidden">
          <EmailTable
            emails={emails?.items || []}
            sort={emailSort}
            onSort={setEmailSort}
            compact
          />
        </div>
      )}

      {tab === "History" && (
        <div className="card-static p-0 overflow-hidden">
          <GitTree
            commits={history?.commits || []}
            branches={history?.branches || []}
          />
        </div>
      )}
    </div>
  );
}

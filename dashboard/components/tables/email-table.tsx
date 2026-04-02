"use client";

import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/data/status-badge";
import { SortableHeader } from "@/components/data/sortable-header";
import { formatDate, truncate } from "@/lib/utils";
import type { EmailLog } from "@/lib/types";
import { ChevronDown, ChevronUp, Trash2, RefreshCw } from "lucide-react";

interface EmailTableProps {
  emails: EmailLog[];
  sort: string;
  onSort: (sort: string) => void;
  compact?: boolean;
}

function EditableField({
  value,
  emailId,
  field,
  multiline,
}: {
  value: string;
  emailId: string;
  field: "subject" | "body";
  multiline?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(value);
  const ref = useRef<HTMLTextAreaElement | HTMLInputElement>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    setText(value);
  }, [value]);

  useEffect(() => {
    if (editing && ref.current) {
      ref.current.focus();
      if (multiline && ref.current instanceof HTMLTextAreaElement) {
        ref.current.style.height = "auto";
        ref.current.style.height = ref.current.scrollHeight + "px";
      }
    }
  }, [editing, multiline]);

  async function save() {
    setEditing(false);
    if (text !== value) {
      await api.updateEmail(emailId, { [field]: text });
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      queryClient.invalidateQueries({ queryKey: ["project-emails"] });
    }
  }

  if (!editing) {
    return multiline ? (
      <pre
        className="text-sm whitespace-pre-wrap leading-relaxed cursor-text hover:bg-[var(--bg-card)] rounded px-2 py-1 -mx-2 -my-1 transition-colors"
        style={{ color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}
        onClick={() => setEditing(true)}
      >
        {text || "—"}
      </pre>
    ) : (
      <p
        className="text-sm cursor-text hover:bg-[var(--bg-card)] rounded px-2 py-1 -mx-2 -my-1 transition-colors"
        style={{ color: "var(--text)" }}
        onClick={() => setEditing(true)}
      >
        {text || "—"}
      </p>
    );
  }

  if (multiline) {
    return (
      <textarea
        ref={ref as React.RefObject<HTMLTextAreaElement>}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          e.target.style.height = "auto";
          e.target.style.height = e.target.scrollHeight + "px";
        }}
        onBlur={save}
        className="w-full text-sm leading-relaxed bg-[var(--bg-card)] border rounded-lg px-3 py-2 outline-none resize-none focus:border-[var(--accent)] focus:shadow-[0_0_0_3px_var(--accent-soft)] transition-all"
        style={{ color: "var(--text-muted)", fontFamily: "var(--font-sans)", borderColor: "var(--border)" }}
      />
    );
  }

  return (
    <input
      ref={ref as React.RefObject<HTMLInputElement>}
      type="text"
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={save}
      onKeyDown={(e) => { if (e.key === "Enter") save(); }}
      className="w-full text-sm bg-[var(--bg-card)] border rounded-lg px-3 py-1.5 outline-none focus:border-[var(--accent)] focus:shadow-[0_0_0_3px_var(--accent-soft)] transition-all"
      style={{ color: "var(--text)", borderColor: "var(--border)" }}
    />
  );
}

export function EmailTable({ emails, sort, onSort, compact }: EmailTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Delete this email?")) return;
    await api.deleteEmail(id);
    queryClient.invalidateQueries({ queryKey: ["emails"] });
    queryClient.invalidateQueries({ queryKey: ["project-emails"] });
    if (expandedId === id) setExpandedId(null);
  }

  async function handleRegenerate(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    const instructions = prompt("What should be changed in this email?");
    if (instructions === null) return;
    await api.regenerateEmail(id, instructions);
    queryClient.invalidateQueries({ queryKey: ["emails"] });
    queryClient.invalidateQueries({ queryKey: ["project-emails"] });
  }

  const columns = [
    { label: "To", key: "to_email" },
    { label: "Subject", key: "subject" },
    { label: "Status", key: "status" },
    ...(!compact
      ? [
          { label: "Company", key: null as string | null },
          { label: "Project", key: null as string | null },
        ]
      : []),
    { label: "Created", key: "created_at" },
    { label: "Sent", key: "sent_at" },
  ];

  const colSpan = columns.length + 2;

  if (emails.length === 0) {
    return (
      <div className="p-10 text-center text-sm" style={{ color: "var(--text-light)" }}>
        No emails yet
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            <th className="px-3 py-3.5 w-8" />
            {columns.map((col) => (
              <SortableHeader key={col.label} label={col.label} sortKey={col.key} currentSort={sort} onSort={onSort} />
            ))}
            <th className="px-3 py-3.5 w-20" />
          </tr>
        </thead>
        <tbody>
          {emails.map((e) => {
            const isDraft = e.status === "draft" || e.status === "pending";
            return (
              <>
                <tr
                  key={e.id}
                  className="transition-colors duration-200 hover:bg-[var(--bg-alt)] cursor-pointer"
                  style={{ borderBottom: expandedId === e.id ? "none" : "1px solid var(--border)" }}
                  onClick={() => setExpandedId(expandedId === e.id ? null : e.id)}
                >
                  <td className="px-3 py-3.5 w-8">
                    {expandedId === e.id
                      ? <ChevronUp size={14} style={{ color: "var(--text-light)" }} />
                      : <ChevronDown size={14} style={{ color: "var(--text-light)" }} />}
                  </td>
                  <td className="px-5 py-3.5 font-data text-xs" style={{ color: "var(--text)" }}>{e.to_email}</td>
                  <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text)" }}>{e.subject ? truncate(e.subject, 50) : "—"}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={e.status} /></td>
                  {!compact && (
                    <>
                      <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-muted)" }}>{e.prospect_company || "—"}</td>
                      <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-muted)" }}>{e.project_name || "—"}</td>
                    </>
                  )}
                  <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(e.created_at)}</td>
                  <td className="px-5 py-3.5 text-xs" style={{ color: "var(--text-light)" }}>{formatDate(e.sent_at)}</td>
                  <td className="px-3 py-3.5">
                    {e.status !== "sent" && (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(ev) => handleRegenerate(e.id, ev)}
                          disabled={e.status === "pending"}
                          className="p-1.5 rounded-full hover:bg-[var(--bg-alt)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                          title={e.status === "pending" ? "Regenerating..." : "Regenerate draft"}
                        >
                          <RefreshCw size={13} style={{ color: "var(--text-light)" }} className={e.status === "pending" ? "animate-spin" : ""} />
                        </button>
                        <button
                          onClick={(ev) => handleDelete(e.id, ev)}
                          className="p-1.5 rounded-full hover:bg-red-50 transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={13} className="text-red-400" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
                {expandedId === e.id && (
                  <tr key={`${e.id}-body`} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td colSpan={colSpan} className="px-8 py-5" style={{ backgroundColor: "var(--bg-alt)" }}>
                      <div className="max-w-2xl">
                        <p className="text-label mb-1.5">Subject</p>
                        {isDraft ? (
                          <EditableField
                            value={e.edited_subject || e.subject || ""}
                            emailId={e.id}
                            field="subject"
                          />
                        ) : (
                          <p className="text-sm" style={{ color: "var(--text)" }}>{e.edited_subject || e.subject || "—"}</p>
                        )}
                        <p className="text-label mb-1.5 mt-4">Body</p>
                        {isDraft ? (
                          <EditableField
                            value={e.edited_body || e.body || ""}
                            emailId={e.id}
                            field="body"
                            multiline
                          />
                        ) : (
                          <pre className="text-sm whitespace-pre-wrap leading-relaxed" style={{ color: "var(--text-muted)", fontFamily: "var(--font-sans)" }}>
                            {e.edited_body || e.body || "—"}
                          </pre>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

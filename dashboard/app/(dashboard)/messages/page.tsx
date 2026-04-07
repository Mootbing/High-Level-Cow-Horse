"use client";

import { useMessages } from "@/lib/hooks/use-api";
import { formatDateTime, cn } from "@/lib/utils";
import { MessageSquare } from "lucide-react";

export default function MessagesPage() {
  const { data, isLoading } = useMessages({ limit: 100 });

  return (
    <div className="space-y-4 animate-in max-w-3xl">
      <div className="card-static">
        <h3 className="text-label flex items-center gap-2 mb-5">
          <MessageSquare size={13} style={{ color: "var(--accent)" }} /> Messages
        </h3>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton h-14 w-full" />
            ))}
          </div>
        ) : data?.items.length ? (
          <div className="space-y-3">
            {data.items.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "max-w-[80%] p-3.5 rounded-[16px]",
                  m.direction === "outbound" ? "ml-auto" : "mr-auto"
                )}
                style={{
                  backgroundColor:
                    m.direction === "outbound"
                      ? "var(--accent-soft)"
                      : "var(--bg-alt)",
                  border: m.direction === "outbound"
                    ? "1px solid rgba(124, 92, 252, 0.12)"
                    : "1px solid var(--border)",
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-medium" style={{ color: "var(--text-light)" }}>
                    {m.direction === "outbound" ? "Sent" : "Received"} &middot; {m.phone_number}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: m.channel === "imessage" ? "rgba(52,199,89,0.12)" : "rgba(37,211,102,0.12)", color: m.channel === "imessage" ? "#34c759" : "#25d366" }}>
                    {m.channel === "imessage" ? "iMessage" : "WhatsApp"}
                  </span>
                  {m.project_name && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: "var(--bg-alt)", color: "var(--text-muted)" }}>
                      {m.project_name}
                    </span>
                  )}
                </div>
                <p className="text-sm" style={{ color: "var(--text)" }}>{m.content || "[media]"}</p>
                <span className="text-[10px] mt-1 block text-right" style={{ color: "var(--text-light)" }}>
                  {formatDateTime(m.created_at)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm py-10 text-center" style={{ color: "var(--text-light)" }}>No messages yet</p>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { EmailLogSummary } from "../types";
import StatusBadge from "../components/StatusBadge";

export default function EmailsPage() {
  const [emails, setEmails] = useState<EmailLogSummary[]>([]);

  useEffect(() => {
    api.emails(100).then(setEmails).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-6">Outbound Emails</h2>

      {emails.length === 0 ? (
        <p className="text-white/40">No emails sent yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-white/40 border-b border-white/5">
                <th className="pb-3 font-medium">To</th>
                <th className="pb-3 font-medium">Subject</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Sent</th>
              </tr>
            </thead>
            <tbody>
              {emails.map((e) => (
                <tr key={e.id} className="border-b border-white/5">
                  <td className="py-3">{e.to_email}</td>
                  <td className="py-3 text-white/60">{e.subject || "-"}</td>
                  <td className="py-3">
                    <StatusBadge status={e.status} />
                  </td>
                  <td className="py-3 text-white/40">
                    {e.sent_at ? new Date(e.sent_at).toLocaleString() : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

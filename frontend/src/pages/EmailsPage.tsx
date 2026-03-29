import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { parseUTC } from "@/lib/utils";
import type { EmailLogSummary } from "../types";
import StatusBadge from "../components/StatusBadge";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../components/ui/table";

interface EditingState {
  id: string;
  subject: string;
  body: string;
}

export default function EmailsPage() {
  const [drafts, setDrafts] = useState<EmailLogSummary[]>([]);
  const [sentEmails, setSentEmails] = useState<EmailLogSummary[]>([]);
  const [editing, setEditing] = useState<EditingState | null>(null);
  const [sending, setSending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDrafts = useCallback(() => {
    api.emailDrafts().then(setDrafts).catch(() => {});
  }, []);

  const loadSent = useCallback(() => {
    api.emails(100, "sent").then(setSentEmails).catch(() => {});
  }, []);

  useEffect(() => {
    loadDrafts();
    loadSent();
  }, [loadDrafts, loadSent]);

  const startEditing = (email: EmailLogSummary) => {
    setEditing({
      id: email.id,
      subject: email.edited_subject || email.subject || "",
      body: email.edited_body || email.body || "",
    });
  };

  const cancelEditing = () => setEditing(null);

  const saveEdit = async () => {
    if (!editing) return;
    setError(null);
    try {
      await api.updateEmailDraft(editing.id, {
        subject: editing.subject,
        body: editing.body,
      });
      setEditing(null);
      loadDrafts();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save edit");
    }
  };

  const sendDraft = async (id: string) => {
    setError(null);
    setSending(id);
    try {
      await api.sendEmailDraft(id);
      loadDrafts();
      loadSent();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send email");
    } finally {
      setSending(null);
    }
  };

  const discardDraft = async (id: string) => {
    setError(null);
    try {
      await api.discardEmailDraft(id);
      loadDrafts();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to discard draft");
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-6 text-foreground">
        Outbound Emails
      </h2>

      {error && (
        <Card className="mb-4 p-3 border-destructive/30 bg-[#1f0a0a]">
          <div className="flex items-center justify-between text-sm text-[#f87171]">
            <span>{error}</span>
            <Button
              variant="ghost"
              size="sm"
              className="text-[#f87171] hover:text-[#fca5a5]"
              onClick={() => setError(null)}
            >
              dismiss
            </Button>
          </div>
        </Card>
      )}

      <Tabs defaultValue="drafts">
        <TabsList>
          <TabsTrigger value="drafts">
            Drafts
            {drafts.length > 0 && (
              <Badge variant="warning" className="ml-2 text-[10px] px-1.5">
                {drafts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="sent">Sent</TabsTrigger>
        </TabsList>

        {/* Drafts Tab */}
        <TabsContent value="drafts">
          {drafts.length === 0 ? (
            <p className="text-muted-foreground mt-4">
              No pending drafts. The outbound agent will create drafts here for
              your review.
            </p>
          ) : (
            <div className="space-y-4 mt-4">
              {drafts.map((draft) => {
                const isEditing = editing?.id === draft.id;
                const isSending = sending === draft.id;
                const displaySubject =
                  draft.edited_subject || draft.subject || "(no subject)";
                const displayBody = draft.edited_body || draft.body || "";

                return (
                  <Card key={draft.id} className="p-5">
                    {/* Header row */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <StatusBadge status="draft" />
                        <span className="text-muted-foreground text-sm">
                          To:{" "}
                          <span className="text-foreground">
                            {draft.to_email}
                          </span>
                        </span>
                      </div>
                      <span className="text-muted-foreground text-xs">
                        {draft.created_at
                          ? parseUTC(draft.created_at)?.toLocaleString()
                          : ""}
                      </span>
                    </div>

                    {isEditing ? (
                      /* Edit mode */
                      <div className="space-y-3">
                        <div>
                          <label className="block text-muted-foreground text-xs mb-1">
                            Subject
                          </label>
                          <Input
                            value={editing.subject}
                            onChange={(e) =>
                              setEditing({
                                ...editing,
                                subject: e.target.value,
                              })
                            }
                          />
                        </div>
                        <div>
                          <label className="block text-muted-foreground text-xs mb-1">
                            Body
                          </label>
                          <Textarea
                            className="min-h-[160px]"
                            value={editing.body}
                            onChange={(e) =>
                              setEditing({
                                ...editing,
                                body: e.target.value,
                              })
                            }
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={saveEdit}>
                            Save Changes
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={cancelEditing}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      /* View mode */
                      <>
                        <div className="mb-2">
                          <span className="text-muted-foreground text-xs">
                            Subject:{" "}
                          </span>
                          <span className="text-foreground text-sm font-medium">
                            {displaySubject}
                          </span>
                        </div>
                        <div className="mb-4 bg-accent/30 rounded-md p-3 text-sm text-muted-foreground max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                          {displayBody}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => sendDraft(draft.id)}
                            disabled={isSending}
                          >
                            {isSending ? "Sending..." : "Send"}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => startEditing(draft)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => discardDraft(draft.id)}
                          >
                            Discard
                          </Button>
                        </div>
                      </>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Sent Tab */}
        <TabsContent value="sent">
          {sentEmails.length === 0 ? (
            <p className="text-muted-foreground mt-4">No emails sent yet.</p>
          ) : (
            <div className="mt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>To</TableHead>
                    <TableHead>Subject</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Sent</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sentEmails.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell className="text-foreground">
                        {e.to_email}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {e.edited_subject || e.subject || "-"}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={e.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {e.sent_at
                          ? parseUTC(e.sent_at)?.toLocaleString()
                          : "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

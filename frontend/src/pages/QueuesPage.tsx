import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { QueueInfo } from "../types";
import { Button } from "../components/ui/button";
import { ChevronDown, ChevronRight, Trash2, X } from "lucide-react";

export default function QueuesPage() {
  const [queues, setQueues] = useState<QueueInfo[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [flushing, setFlushing] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(() => {
    api.queues().then(setQueues).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    pollRef.current = setInterval(load, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [load]);

  const toggleExpand = (agentType: string) => {
    setExpanded((prev) => ({ ...prev, [agentType]: !prev[agentType] }));
  };

  const handleFlushAll = async () => {
    if (!confirm("Flush ALL agent queues? This cannot be undone.")) return;
    setFlushing("all");
    try {
      await api.flushAllQueues();
      load();
    } catch {
      // ignore
    } finally {
      setFlushing(null);
    }
  };

  const handleFlush = async (agentType: string) => {
    if (!confirm(`Flush queue for ${agentType}?`)) return;
    setFlushing(agentType);
    try {
      await api.flushQueue(agentType);
      load();
    } catch {
      // ignore
    } finally {
      setFlushing(null);
    }
  };

  const handleCancel = async (agentType: string, entryId: string) => {
    setCancelling(entryId);
    try {
      await api.cancelQueueMessage(agentType, entryId);
      load();
    } catch {
      // ignore
    } finally {
      setCancelling(null);
    }
  };

  const totalMessages = queues.reduce(
    (sum, q) => sum + (q.stream_length ?? 0),
    0
  );

  return (
    <div className="p-8 max-w-[1200px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">Agent Queues</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {queues.length} queues &middot; {totalMessages} total messages
          </p>
        </div>
        <Button
          variant="destructive"
          size="sm"
          disabled={flushing === "all" || totalMessages === 0}
          onClick={handleFlushAll}
        >
          <Trash2 className="w-4 h-4 mr-1" />
          {flushing === "all" ? "Flushing..." : "Flush All"}
        </Button>
      </div>

      <div className="space-y-3">
        {queues.map((q) => (
          <div
            key={q.agent_type}
            className="bg-card/50 border border-border rounded-lg overflow-hidden"
          >
            {/* Queue header */}
            <div
              className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-accent/30 transition-colors"
              onClick={() => toggleExpand(q.agent_type)}
            >
              <div className="flex items-center gap-3">
                {expanded[q.agent_type] ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
                <span className="font-mono font-semibold text-sm text-foreground">
                  {q.agent_type}
                </span>
                {q.error ? (
                  <span className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded px-2 py-0.5">
                    Error
                  </span>
                ) : (
                  <span
                    className={`text-xs rounded px-2 py-0.5 ${
                      (q.stream_length ?? 0) > 0
                        ? "text-amber-400 bg-amber-400/10 border border-amber-400/20"
                        : "text-muted-foreground bg-muted/30 border border-border"
                    }`}
                  >
                    {q.stream_length ?? 0} msgs
                  </span>
                )}
                {(q.pending ?? 0) > 0 && (
                  <span className="text-xs text-blue-400 bg-blue-400/10 border border-blue-400/20 rounded px-2 py-0.5">
                    {q.pending} pending
                  </span>
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-red-400 h-7 px-2"
                disabled={
                  flushing === q.agent_type || (q.stream_length ?? 0) === 0
                }
                onClick={(e) => {
                  e.stopPropagation();
                  handleFlush(q.agent_type);
                }}
              >
                <Trash2 className="w-3.5 h-3.5 mr-1" />
                {flushing === q.agent_type ? "..." : "Flush"}
              </Button>
            </div>

            {/* Expanded messages */}
            {expanded[q.agent_type] && (
              <div className="border-t border-border">
                {q.error ? (
                  <div className="px-4 py-3 text-sm text-red-400">
                    {q.error}
                  </div>
                ) : !q.messages || q.messages.length === 0 ? (
                  <div className="px-4 py-4 text-sm text-muted-foreground/50 text-center">
                    Queue is empty
                  </div>
                ) : (
                  <div className="divide-y divide-border">
                    {q.messages.map((msg) => (
                      <div
                        key={msg.entry_id}
                        className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] group"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            {msg.type && (
                              <span className="text-xs font-mono font-semibold text-blue-400">
                                {msg.type}
                              </span>
                            )}
                            {msg.source && (
                              <span className="text-xs text-muted-foreground">
                                from {msg.source}
                              </span>
                            )}
                            <span className="text-[10px] text-muted-foreground/40 font-mono">
                              {msg.entry_id}
                            </span>
                          </div>
                          {msg.preview ? (
                            <p className="text-xs text-foreground/60 truncate max-w-[700px]">
                              {msg.preview}
                            </p>
                          ) : msg.raw ? (
                            <p className="text-xs text-foreground/40 truncate max-w-[700px] font-mono">
                              {msg.raw}
                            </p>
                          ) : null}
                        </div>
                        <button
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-red-400 p-1 rounded"
                          disabled={cancelling === msg.entry_id}
                          onClick={() =>
                            handleCancel(q.agent_type, msg.entry_id)
                          }
                          title="Cancel this message"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {queues.length === 0 && (
          <div className="text-center text-muted-foreground/50 py-16 text-sm">
            Loading queues...
          </div>
        )}
      </div>
    </div>
  );
}

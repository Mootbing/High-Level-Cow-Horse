import { useEffect, useRef, useState, useCallback } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../api/client";
import type { ChatMessage } from "../types";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { cn, parseUTC } from "@/lib/utils";
import { Send } from "lucide-react";

/**
 * A "pending" message is one shown immediately in the UI before the next
 * poll confirms it exists in the database.  Two flavours:
 *   - user-sent  (direction "inbound")
 *   - agent-reply via WebSocket (direction "outbound")
 *
 * Once a poll returns a history message whose content matches a pending
 * message, the pending entry is dropped — history is the source of truth.
 */
interface PendingMessage {
  /** Temporary client-side id so React keys stay stable. */
  _clientId: string;
  direction: "inbound" | "outbound";
  content: string;
  media_url?: string;
  created_at: string;
}

let _nextClientId = 0;
function makeClientId() {
  return `pending-${++_nextClientId}-${Date.now()}`;
}

export default function ChatPage() {
  const { connected, messages: wsMessages, sendMessage, clearMessages } =
    useWebSocket();
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState<PendingMessage[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Track which WS messages we have already promoted to pending so we
  // don't re-add them on every render.
  const processedWsCount = useRef(0);

  // ── Poll history every 5 s (source of truth) ─────────────────────────
  useEffect(() => {
    const loadHistory = () => {
      api
        .messages(100)
        .then((msgs) => {
          const sorted = msgs.reverse(); // oldest-first
          setHistory(sorted);

          // Reconcile: drop any pending message whose content now appears
          // in polled history.  We match on content because the server
          // does not echo back a client-side id.
          setPending((prev) => {
            if (prev.length === 0) return prev;

            // Build a set of content strings present in history for fast lookup.
            const historyContents = new Set(
              sorted.map((m) => m.content?.trim())
            );

            const remaining = prev.filter(
              (p) => !historyContents.has(p.content.trim())
            );
            return remaining.length === prev.length ? prev : remaining;
          });
        })
        .catch(() => {});
    };

    loadHistory();
    const interval = setInterval(loadHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  // ── Promote incoming WS agent replies to pending ─────────────────────
  useEffect(() => {
    if (wsMessages.length <= processedWsCount.current) return;

    const newWs = wsMessages.slice(processedWsCount.current);
    processedWsCount.current = wsMessages.length;

    const agentReplies = newWs.filter((m) => m.type === "chat");
    if (agentReplies.length === 0) return;

    setPending((prev) => [
      ...prev,
      ...agentReplies.map((m) => ({
        _clientId: makeClientId(),
        direction: "outbound" as const,
        content: m.content ?? "",
        media_url: m.media_url,
        created_at: new Date().toISOString(),
      })),
    ]);
  }, [wsMessages]);

  // ── Auto-scroll on any change ────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, pending]);

  // ── Send handler ─────────────────────────────────────────────────────
  const handleSend = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const text = input.trim();
      if (!text) return;

      sendMessage(text);

      setPending((prev) => [
        ...prev,
        {
          _clientId: makeClientId(),
          direction: "inbound",
          content: text,
          created_at: new Date().toISOString(),
        },
      ]);
      setInput("");
    },
    [input, sendMessage]
  );

  // ── Build unified, time-sorted message list ──────────────────────────
  type UnifiedMessage = {
    key: string;
    direction: string;
    content: string | null;
    media_url?: string | null;
    created_at: string | null;
    isPending?: boolean;
  };

  const unified: UnifiedMessage[] = [
    ...history.map((m) => ({
      key: m.id,
      direction: m.direction,
      content: m.content,
      media_url: m.media_url,
      created_at: m.created_at,
    })),
    ...pending.map((p) => ({
      key: p._clientId,
      direction: p.direction,
      content: p.content,
      media_url: p.media_url ?? null,
      created_at: p.created_at,
      isPending: true,
    })),
  ].sort(
    (a, b) =>
      new Date(a.created_at ?? 0).getTime() -
      new Date(b.created_at ?? 0).getTime()
  );

  // ── Render ───────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-foreground">
            Chat with CEO Agent
          </h2>
          <p className="text-xs text-muted-foreground">
            {connected ? "Connected" : "Reconnecting..."}
          </p>
        </div>
        <span
          className={cn(
            "w-2.5 h-2.5 rounded-full",
            connected ? "bg-[#4ade80]" : "bg-[#f87171]"
          )}
        />
      </div>

      {/* Messages — single unified list */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-3">
        {unified.map((msg) => {
          const isInbound = msg.direction === "inbound";
          return (
            <div
              key={msg.key}
              className={cn(
                "max-w-[70%]",
                isInbound ? "ml-auto" : "mr-auto"
              )}
            >
              <div
                className={cn(
                  "rounded-2xl px-4 py-2.5 text-sm",
                  isInbound
                    ? "bg-foreground text-background"
                    : "bg-card border border-border text-foreground",
                  msg.isPending && "opacity-70"
                )}
              >
                {msg.content}
              </div>
              {msg.media_url && (
                <img
                  src={msg.media_url}
                  alt=""
                  className="mt-2 rounded-lg max-w-full"
                />
              )}
              <p className="text-[10px] text-muted-foreground mt-1 px-1">
                {msg.created_at
                  ? parseUTC(msg.created_at)?.toLocaleTimeString()
                  : ""}
              </p>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="px-6 py-4 border-t border-border">
        <div className="flex gap-3">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Send a message to your AI agency..."
            className="flex-1 h-11 rounded-xl"
            autoFocus
          />
          <Button type="submit" className="h-11 px-5 rounded-xl">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}

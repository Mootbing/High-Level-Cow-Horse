import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../api/client";
import type { ChatMessage } from "../types";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { cn } from "@/lib/utils";
import { Send } from "lucide-react";

export default function ChatPage() {
  const { connected, messages: wsMessages, sendMessage } = useWebSocket();
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [sentMessages, setSentMessages] = useState<
    { content: string; ts: string }[]
  >([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .messages(100)
      .then((msgs) => setHistory(msgs.reverse()))
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [wsMessages, sentMessages, history]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    sendMessage(text);
    setSentMessages((prev) => [
      ...prev,
      { content: text, ts: new Date().toISOString() },
    ]);
    setInput("");
  }

  const agentReplies = wsMessages.filter((m) => m.type === "chat");

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

      {/* Messages */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-3">
        {/* History */}
        {history.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "max-w-[70%]",
              msg.direction === "inbound" ? "ml-auto" : "mr-auto"
            )}
          >
            <div
              className={cn(
                "rounded-2xl px-4 py-2.5 text-sm",
                msg.direction === "inbound"
                  ? "bg-foreground text-background"
                  : "bg-card border border-border text-foreground"
              )}
            >
              {msg.content}
            </div>
            <p className="text-[10px] text-muted-foreground mt-1 px-1">
              {msg.created_at
                ? new Date(msg.created_at).toLocaleTimeString()
                : ""}
            </p>
          </div>
        ))}

        {/* Sent messages (this session) */}
        {sentMessages.map((msg, i) => (
          <div key={`sent-${i}`} className="max-w-[70%] ml-auto">
            <div className="rounded-2xl px-4 py-2.5 text-sm bg-foreground text-background">
              {msg.content}
            </div>
            <p className="text-[10px] text-muted-foreground mt-1 px-1">
              {new Date(msg.ts).toLocaleTimeString()}
            </p>
          </div>
        ))}

        {/* Agent replies (this session) */}
        {agentReplies.map((msg, i) => (
          <div key={`ws-${i}`} className="max-w-[70%] mr-auto">
            <div className="rounded-2xl px-4 py-2.5 text-sm bg-card border border-border text-foreground">
              {msg.content}
            </div>
            {msg.media_url && (
              <img
                src={msg.media_url}
                alt=""
                className="mt-2 rounded-lg max-w-full"
              />
            )}
          </div>
        ))}

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

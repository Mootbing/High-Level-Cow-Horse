import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../api/client";
import type { ChatMessage } from "../types";

export default function ChatPage() {
  const { connected, messages: wsMessages, sendMessage } = useWebSocket();
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [sentMessages, setSentMessages] = useState<{ content: string; ts: string }[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount
  useEffect(() => {
    api.messages(100).then((msgs) => setHistory(msgs.reverse())).catch(() => {});
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [wsMessages, sentMessages, history]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    sendMessage(text);
    setSentMessages((prev) => [...prev, { content: text, ts: new Date().toISOString() }]);
    setInput("");
  }

  // Merge history + live messages
  const agentReplies = wsMessages.filter((m) => m.type === "chat");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">Chat with CEO Agent</h2>
          <p className="text-xs text-white/40">
            {connected ? "Connected" : "Reconnecting..."}
          </p>
        </div>
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            connected ? "bg-green-400" : "bg-red-400"
          }`}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-3">
        {/* History */}
        {history.map((msg) => (
          <div
            key={msg.id}
            className={`max-w-[70%] ${
              msg.direction === "inbound" ? "ml-auto" : "mr-auto"
            }`}
          >
            <div
              className={`rounded-2xl px-4 py-2.5 text-sm ${
                msg.direction === "inbound"
                  ? "bg-brand-600 text-white"
                  : "bg-white/10 text-white"
              }`}
            >
              {msg.content}
            </div>
            <p className="text-[10px] text-white/20 mt-1 px-1">
              {msg.created_at
                ? new Date(msg.created_at).toLocaleTimeString()
                : ""}
            </p>
          </div>
        ))}

        {/* Sent messages (this session) */}
        {sentMessages.map((msg, i) => (
          <div key={`sent-${i}`} className="max-w-[70%] ml-auto">
            <div className="rounded-2xl px-4 py-2.5 text-sm bg-brand-600 text-white">
              {msg.content}
            </div>
            <p className="text-[10px] text-white/20 mt-1 px-1">
              {new Date(msg.ts).toLocaleTimeString()}
            </p>
          </div>
        ))}

        {/* Agent replies (this session) */}
        {agentReplies.map((msg, i) => (
          <div key={`ws-${i}`} className="max-w-[70%] mr-auto">
            <div className="rounded-2xl px-4 py-2.5 text-sm bg-white/10 text-white">
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
      <form onSubmit={handleSend} className="px-6 py-4 border-t border-white/5">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Send a message to your AI agency..."
            className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-brand-500"
            autoFocus
          />
          <button
            type="submit"
            className="px-6 py-3 bg-brand-600 hover:bg-brand-700 rounded-xl font-medium transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

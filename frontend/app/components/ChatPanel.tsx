"use client";
import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "../../lib/types";
import RecommendationCard from "./RecommendationCard";

export default function ChatPanel({
  messages,
  onSend,
  loading,
}: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  loading: boolean;
}) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = () => {
    if (!input.trim()) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xl space-y-3 ${m.role === "user" ? "" : "w-full"}`}>
              {m.content && (
                <div
                  className={`rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-emerald-700/30 border border-emerald-700/50 text-emerald-100"
                      : "bg-neutral-900 border border-neutral-800 text-neutral-200"
                  }`}
                >
                  {m.content}
                </div>
              )}
              {m.recommendations?.map((rec, j) => (
                <RecommendationCard key={j} rec={rec} />
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-xs text-neutral-500">Reasoning…</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-neutral-800 p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Describe your land, soil, or biodiversity concern…"
          className="flex-1 rounded-lg bg-neutral-900 border border-neutral-800 px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-600 focus:outline-none focus:border-emerald-600"
        />
        <button
          onClick={submit}
          className="rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm px-4 py-2 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
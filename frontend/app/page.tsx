"use client";
import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import MetricsPanel from "./components/MetricsPanel";
import EvidencePanel from "./components/EvidencePanel";
import MetricRadarChart from "./components/MetricRadarChart";
import { converse, diagnose } from "../lib/api";
import { ChatMessage, EnvironmentalInput, Recommendation } from "../lib/types";


const SESSION_ID = "demo-session-1"; // swap for a generated UUID per browser session


export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Tell me about your land, soil, or biodiversity concern — e.g. \"Soil organic carbon is 0.3%, rainfall is low, we grow monoculture wheat in a semi-arid region.\"",
    },
  ]);
  const [filledInput, setFilledInput] = useState<EnvironmentalInput | null>(null);
  const [allRecs, setAllRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (text: string) => {
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await converse(SESSION_ID, text);
      setFilledInput(res.filled_input || null);
      if (res.recommendations?.length) {
        setAllRecs((prev) => [...prev, ...res.recommendations]);
      }
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.recommendations?.length ? "" : res.reply_text,
          recommendations: res.recommendations?.length ? res.recommendations : undefined,
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Couldn't reach the reasoning API — is the backend running on :8000?" },
      ]);
    } finally {
      setLoading(false);
    }
  };
  // inside Home(), alongside your existing state
const [geo, setGeo] = useState<{ lat?: number; lon?: number }>({});

const handleGeoChange = (field: "lat" | "lon", value: number) => {
  const next = { ...geo, [field]: value };
  setGeo(next);
  if (next.lat !== undefined && next.lon !== undefined && !isNaN(next.lat) && !isNaN(next.lon)) {
    const { region_biome, ...rest } = filledInput || {};
    diagnose(SESSION_ID, { ...rest, lat: next.lat, lon: next.lon }).then((res) => {
      setFilledInput(res.filled_input || null);
    });
  }
};

  

  return (
    <main className="h-screen flex flex-col bg-neutral-950">
      <header className="border-b border-neutral-800 px-4 py-3">
        <h1 className="text-sm font-semibold text-neutral-200">
          🌱 Darukaa.Earth — Biodiversity Intelligence
        </h1>
      </header>
      <div className="flex flex-1 min-h-0">
        <div className="flex flex-col">
          <MetricsPanel filled={filledInput} onGeoChange={handleGeoChange} />
          <div className="w-72 shrink-0 border-r border-t border-neutral-800 p-4">
            <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wide mb-2">
              Metric Balance
            </h2>
            <MetricRadarChart filled={filledInput} />
          </div>
        </div>
        <ChatPanel messages={messages} onSend={handleSend} loading={loading} />
        <EvidencePanel recommendations={allRecs} />
      </div>
    </main>
  );
}

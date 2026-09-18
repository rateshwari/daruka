import { SystemResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://darukaa-api-yml0.onrender.com";
export async function converse(sessionId: string, message: string): Promise<SystemResponse> {
  const res = await fetch(`${API_BASE}/converse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function diagnose(sessionId: string, data: Record<string, unknown>): Promise<SystemResponse> {
  const res = await fetch(`${API_BASE}/diagnose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, data }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

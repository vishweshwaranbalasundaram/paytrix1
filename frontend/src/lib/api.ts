const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Demo agent identity — seeded server-side on startup. In a real deployment
// each AI agent would get its own provisioned key, never a shared demo one.
const AGENT_ID = process.env.NEXT_PUBLIC_AGENT_ID || "agt_demo_ui";
const AGENT_KEY = process.env.NEXT_PUBLIC_AGENT_KEY || "demo_agent_secret_key_do_not_use_in_prod";

const AGENT_HEADERS = {
  "Content-Type": "application/json",
  "X-Agent-Id": AGENT_ID,
  "X-Agent-Key": AGENT_KEY,
};

export async function getHealth() {
  const res = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function getLedger() {
  const res = await fetch(`${API_BASE_URL}/api/v1/agent/ledger`);
  if (!res.ok) throw new Error("Ledger fetch failed");
  return res.json();
}

export async function postCheckout(payload: unknown) {
  const res = await fetch(`${API_BASE_URL}/api/v1/agent/checkout`, {
    method: "POST",
    headers: AGENT_HEADERS,
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function postConfirm(trace_id: string, confirmation_token: string) {
  const res = await fetch(`${API_BASE_URL}/api/v1/agent/confirm`, {
    method: "POST",
    headers: AGENT_HEADERS,
    body: JSON.stringify({ trace_id, confirmation_token }),
  });
  return res.json();
}

export { AGENT_HEADERS, API_BASE_URL };

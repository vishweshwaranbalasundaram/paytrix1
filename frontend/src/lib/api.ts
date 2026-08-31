const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export { API_BASE_URL };

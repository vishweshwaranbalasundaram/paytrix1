"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  RefreshCw,
  FileText,
  Zap,
  Database,
  CheckCircle2,
  XCircle,
  Copy,
  Terminal,
  Activity,
} from "lucide-react";

type Proposal = {
  product_id: string;
  product_name: string;
  category: string;
  price_paise: number;
  baseline_price_paise: number;
  merchant_trust_score: number;
  product_rating: number;
  has_hidden_subscription: boolean;
};

type CheckoutPayload = {
  user_id: string;
  user_prompt: string;
  trace_id: string;
  intent_envelope: {
    target_price_paise: number;
    ceiling_price_paise: number;
    min_merchant_trust_score: number;
    required_category: string;
    allow_recurring_subscriptions: boolean;
  };
  proposal: Proposal;
};

type LedgerEntry = {
  id: number;
  trace_id: string;
  event_type: string;
  status: string;
  amount_paise: number;
  payload_hash: string;
  previous_hash: string;
};

export default function PaytrixAppleDashboard() {
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState<any>(null);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [backendStatus, setBackendStatus] = useState<"connected" | "offline">("offline");
  const [copied, setCopied] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/health`);
        if (res.ok) {
          setBackendStatus("connected");
          fetchLedger();
        } else {
          setBackendStatus("offline");
        }
      } catch {
        setBackendStatus("offline");
      }
    };
    checkHealth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchLedger = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/agent/ledger`);
      const data = await res.json();
      if (data.ledger) setLedger(data.ledger);
    } catch (e) {
      console.error("Ledger fetch error", e);
    }
  };

  const runSimulation = async (scenario: "happy" | "dark_pattern" | "scalping") => {
    setLoading(true);
    const payload: CheckoutPayload = {
      user_id: "usr_demo_123",
      user_prompt: "Order monthly diabetes care supplies under \u20b91,500",
      trace_id: `tr_apple_${Date.now()}`,
      intent_envelope: {
        target_price_paise: 150000,
        ceiling_price_paise: 160000,
        min_merchant_trust_score: 0.8,
        required_category: "pharmacy",
        allow_recurring_subscriptions: false,
      },
      proposal: {
        product_id: "MED_101",
        product_name: "Diabetes Care Pack",
        category: "pharmacy",
        price_paise: 145000,
        baseline_price_paise: 145000,
        merchant_trust_score: 0.95,
        product_rating: 4.8,
        has_hidden_subscription: false,
      },
    };

    if (scenario === "dark_pattern") {
      payload.proposal.product_name = "Diabetes Care + Secret Club (\u20b9299/mo)";
      payload.proposal.has_hidden_subscription = true;
    } else if (scenario === "scalping") {
      payload.proposal.price_paise = 185000; // >10% over 145000 baseline
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/agent/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setLastResponse(data);
      fetchLedger();
    } catch (err) {
      setLastResponse({
        status: "ERROR",
        reason: "Failed to connect to backend server on port 8000",
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-cyan-500/30 font-sans pb-16">
      {/* Dynamic Background Glows */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="fixed top-1/3 right-1/4 w-[30rem] h-[30rem] bg-emerald-500/5 rounded-full blur-[140px] pointer-events-none" />

      {/* Navigation Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/60 border-b border-white/10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-emerald-500/20 border border-white/10 shadow-inner">
              <Lock className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  PAYTRIX
                </h1>
                <span className="text-[10px] uppercase font-mono tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  v1.0 Safety Mesh
                </span>
              </div>
              <p className="text-xs text-slate-400">Autonomous UPI Micro-Mandates</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/10 text-xs font-mono backdrop-blur-md">
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === "connected" ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
                }`}
              />
              <span className="text-slate-300">
                Kernel: {backendStatus === "connected" ? "Active (8000)" : "Offline"}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-6 pt-10 space-y-8">
        {/* Hero Section */}
        <section className="relative overflow-hidden p-8 rounded-3xl bg-slate-900/30 border border-white/10 backdrop-blur-2xl shadow-2xl">
          <div className="max-w-2xl space-y-4">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-b from-white to-slate-300 bg-clip-text text-transparent">
              Money follows verified intent&mdash;never AI hallucinations.
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              PAYTRIX intercepts agent purchasing proposals before they touch payment gateways
              using deterministic I2A rules, price sentinels, and HMAC signed receipts.
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-white/5 backdrop-blur-md">
              <ShieldCheck className="w-5 h-5 text-emerald-400 mb-2" />
              <div className="text-xl font-bold font-mono">100%</div>
              <div className="text-[11px] text-slate-400">Gateway Isolation</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-white/5 backdrop-blur-md">
              <Zap className="w-5 h-5 text-cyan-400 mb-2" />
              <div className="text-xl font-bold font-mono">&ge; 85%</div>
              <div className="text-[11px] text-slate-400">Auto-Execute Score</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-white/5 backdrop-blur-md">
              <Activity className="w-5 h-5 text-rose-400 mb-2" />
              <div className="text-xl font-bold font-mono">+10% Cap</div>
              <div className="text-[11px] text-slate-400">Price Scalping Guard</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-white/5 backdrop-blur-md">
              <Database className="w-5 h-5 text-amber-400 mb-2" />
              <div className="text-xl font-bold font-mono">SHA-256</div>
              <div className="text-[11px] text-slate-400">Cryptographic Chain</div>
            </div>
          </div>
        </section>

        {/* Command Center: Failure Lab & Live Telemetry */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Failure Lab Controls */}
          <section className="p-6 rounded-3xl bg-slate-900/40 border border-white/10 backdrop-blur-2xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-cyan-400" />
                <h3 className="font-semibold text-slate-200">Interactive Failure Lab</h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">Agent Attack Simulator</span>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => runSimulation("happy")}
                disabled={loading}
                className="w-full p-4 rounded-2xl bg-gradient-to-r from-blue-600/20 to-cyan-600/20 hover:from-blue-600/30 hover:to-cyan-600/30 border border-cyan-500/30 text-left flex items-center justify-between group transition-all disabled:opacity-50"
              >
                <div>
                  <div className="font-medium text-sm text-cyan-200">Valid Purchase Scenario</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Diabetes Medicine Order (₹1,450 / Score: 97%)
                  </div>
                </div>
                <CheckCircle2 className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
              </button>

              <button
                onClick={() => runSimulation("dark_pattern")}
                disabled={loading}
                className="w-full p-4 rounded-2xl bg-rose-950/20 hover:bg-rose-950/30 border border-rose-500/30 text-left flex items-center justify-between group transition-all disabled:opacity-50"
              >
                <div>
                  <div className="font-medium text-sm text-rose-200">Simulate Dark Pattern Trap</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Hidden Auto-Renew Subscription (₹299/mo)
                  </div>
                </div>
                <ShieldAlert className="w-5 h-5 text-rose-400 group-hover:scale-110 transition-transform" />
              </button>

              <button
                onClick={() => runSimulation("scalping")}
                disabled={loading}
                className="w-full p-4 rounded-2xl bg-amber-950/20 hover:bg-amber-950/30 border border-amber-500/30 text-left flex items-center justify-between group transition-all disabled:opacity-50"
              >
                <div>
                  <div className="font-medium text-sm text-amber-200">
                    Simulate Dynamic Price Scalping
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Price marked up to ₹1,850 (+27.5% over baseline)
                  </div>
                </div>
                <XCircle className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
              </button>
            </div>
          </section>

          {/* Telemetry Output */}
          <section className="p-6 rounded-3xl bg-slate-900/40 border border-white/10 backdrop-blur-2xl space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-white/5">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold text-slate-200">Kernel Response & PrNE Telemetry</h3>
              </div>
              {loading && <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin" />}
            </div>

            {lastResponse ? (
              <div className="space-y-4">
                {/* Status Badge */}
                <div
                  className={`p-4 rounded-2xl border backdrop-blur-md ${
                    lastResponse.status === "COMPLETED" || lastResponse.status === "AUTO_EXECUTE"
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                      : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs">
                    <span className="font-bold text-sm">STATUS: {lastResponse.status}</span>
                    <span>Razorpay Called: {lastResponse.razorpay_called ? "TRUE (1)" : "FALSE (0)"}</span>
                  </div>
                  {lastResponse.reason && (
                    <div className="text-xs font-mono text-rose-400 mt-2">
                      Reason: {lastResponse.reason}
                    </div>
                  )}
                </div>

                {/* Cryptographic PrNE Receipt */}
                {lastResponse.proof_of_non_execution && (
                  <div className="p-4 rounded-2xl bg-slate-950/80 border border-amber-500/30 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-amber-400">
                      <span className="flex items-center gap-1.5">
                        <Lock className="w-3.5 h-3.5" /> Proof of Non-Execution (PrNE)
                      </span>
                      <button
                        onClick={() => copyToClipboard(lastResponse.proof_of_non_execution)}
                        className="hover:text-amber-300 transition-colors"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="text-[11px] font-mono break-all text-slate-400 bg-slate-900/60 p-2.5 rounded-xl border border-white/5">
                      {lastResponse.proof_of_non_execution}
                    </div>
                    {copied && <div className="text-[10px] text-amber-400">Copied to clipboard</div>}
                  </div>
                )}

                {/* Raw Payload Stream */}
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-white/5 overflow-x-auto">
                  <pre className="text-xs font-mono text-slate-400">
                    {JSON.stringify(lastResponse, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500 text-xs font-mono">
                Trigger a scenario on the left to inspect real-time kernel telemetry.
              </div>
            )}
          </section>
        </div>

        {/* Cryptographic Audit Ledger */}
        <section className="p-6 rounded-3xl bg-slate-900/40 border border-white/10 backdrop-blur-2xl space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-amber-400" />
              <h3 className="font-semibold text-slate-200">Cryptographic Audit Ledger (SHA-256 Hash Chained)</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">{ledger.length} Block Entries</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="text-slate-500 border-b border-white/5">
                  <th className="pb-3 px-2">ID</th>
                  <th className="pb-3 px-2">Trace ID</th>
                  <th className="pb-3 px-2">Event</th>
                  <th className="pb-3 px-2">Status</th>
                  <th className="pb-3 px-2">Payload Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {ledger.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-2 text-slate-500">#{item.id}</td>
                    <td className="py-3 px-2 text-cyan-400">{item.trace_id}</td>
                    <td className="py-3 px-2">{item.event_type}</td>
                    <td className="py-3 px-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] ${
                          item.status === "COMPLETED"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-rose-500/10 text-rose-400"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-slate-500 truncate max-w-[200px]">
                      {item.payload_hash}
                    </td>
                  </tr>
                ))}
                {ledger.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-600">
                      No ledger blocks recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

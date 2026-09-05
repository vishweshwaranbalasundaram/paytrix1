"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  ArrowRight,
  Check,
  X,
  Download,
  AlertTriangle,
  Settings,
  Bot,
  ExternalLink,
} from "lucide-react";
import { getLedger, postCheckout, postConfirm } from "@/lib/api";

const FONT_LINK_ID = "paytrix-fonts";

function useFonts() {
  useEffect(() => {
    if (document.getElementById(FONT_LINK_ID)) return;
    const link = document.createElement("link");
    link.id = FONT_LINK_ID;
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap";
    document.head.appendChild(link);
  }, []);
}

const COLORS = {
  bg: "#0A0D14",
  panel: "rgba(13,17,23,0.72)",
  indigo: "#6366F1",
  emerald: "#10B981",
  amber: "#F59E0B",
  rose: "#F43F5E",
  text: "rgba(255,255,255,0.92)",
  textDim: "rgba(255,255,255,0.55)",
  border: "rgba(255,255,255,0.10)",
};

function ParticleField({ reducedMotion }: { reducedMotion: boolean }) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reducedMotion) return;
    let renderer: any, scene: any, camera: any, points: any, frameId: number;
    let width: number, height: number;
    let mouseX = 0,
      mouseY = 0;

    async function init() {
      const THREE = await import("three");
      const mount = mountRef.current;
      if (!mount) return;
      width = mount.clientWidth;
      height = mount.clientHeight;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
      camera.position.z = 60;

      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      mount.appendChild(renderer.domElement);

      const count = 220;
      const positions = new Float32Array(count * 3);
      const colors = new Float32Array(count * 3);
      const palette = [
        [0.39, 0.4, 0.95],
        [0.06, 0.72, 0.5],
      ];
      for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 140;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 90;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 80;
        const c = palette[Math.random() > 0.6 ? 1 : 0];
        colors[i * 3] = c[0];
        colors[i * 3 + 1] = c[1];
        colors[i * 3 + 2] = c[2];
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
      const material = new THREE.PointsMaterial({
        size: 1.6,
        vertexColors: true,
        transparent: true,
        opacity: 0.75,
        depthWrite: false,
      });
      points = new THREE.Points(geometry, material);
      scene.add(points);

      const onMove = (e: MouseEvent) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
      };
      window.addEventListener("mousemove", onMove);

      const animate = () => {
        points.rotation.y += 0.0009;
        points.rotation.x += 0.0002;
        camera.position.x += (mouseX * 8 - camera.position.x) * 0.02;
        camera.position.y += (-mouseY * 5 - camera.position.y) * 0.02;
        camera.lookAt(0, 0, 0);
        renderer.render(scene, camera);
        frameId = requestAnimationFrame(animate);
      };
      animate();

      const onResize = () => {
        if (!mount) return;
        width = mount.clientWidth;
        height = mount.clientHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
      };
      window.addEventListener("resize", onResize);

      return () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("resize", onResize);
      };
    }

    let cleanupFn: any;
    init().then((c) => (cleanupFn = c));

    return () => {
      if (frameId) cancelAnimationFrame(frameId);
      if (cleanupFn) cleanupFn();
      if (renderer) {
        renderer.dispose();
        if (mountRef.current && renderer.domElement.parentNode === mountRef.current) {
          mountRef.current.removeChild(renderer.domElement);
        }
      }
    };
  }, [reducedMotion]);

  return (
    <div
      ref={mountRef}
      style={{ position: "absolute", inset: 0, zIndex: 0, pointerEvents: "none" }}
    />
  );
}

function TiltCard({
  requestText,
  amount,
  accentColor,
  reducedMotion,
}: {
  requestText: string;
  amount: number;
  accentColor: string;
  reducedMotion: boolean;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const onMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (reducedMotion) return;
      const el = cardRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width - 0.5;
      const py = (e.clientY - rect.top) / rect.height - 0.5;
      setTilt({ x: py * -14, y: px * 16 });
    },
    [reducedMotion]
  );

  const reset = () => setTilt({ x: 0, y: 0 });

  return (
    <div style={{ perspective: "1000px" }}>
      <div
        ref={cardRef}
        onMouseMove={onMouseMove}
        onMouseLeave={reset}
        style={{
          width: 320,
          height: 190,
          borderRadius: 20,
          background: "linear-gradient(135deg, rgba(99,102,241,0.22), rgba(16,185,129,0.10))",
          border: `1px solid ${COLORS.border}`,
          backdropFilter: "blur(18px)",
          transform: reducedMotion ? "none" : `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
          transition: "transform 0.15s ease-out",
          padding: "22px 24px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxShadow: "0 20px 60px -20px rgba(99,102,241,0.45)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 15, color: COLORS.text }}>
            Paytrix
          </span>
          <ShieldCheck size={20} color={accentColor} />
        </div>
        <div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: COLORS.textDim, marginBottom: 4 }}>
            Agent request
          </div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              color: COLORS.text,
              letterSpacing: 0.3,
              lineHeight: 1.4,
              maxHeight: 38,
              overflow: "hidden",
            }}
          >
            {requestText}
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: COLORS.textDim }}>
            Safety Kernel · hold
          </span>
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 18, color: COLORS.text }}>
            ₹{amount}
          </span>
        </div>
      </div>
    </div>
  );
}

const BOOT_LINES = [
  "Booting Paytrix Safety Kernel",
  "Loading policy & risk engine",
  "Warming up the audit ledger",
  "Ready",
];

function IntroSplash({ onDone, reducedMotion }: { onDone: () => void; reducedMotion: boolean }) {
  const [progress, setProgress] = useState(0);
  const [line, setLine] = useState(0);

  useEffect(() => {
    if (reducedMotion) {
      onDone();
      return;
    }
    const duration = 1900;
    const start = performance.now();
    let raf: number;
    const tick = (now: number) => {
      const pct = Math.min(100, ((now - start) / duration) * 100);
      setProgress(pct);
      setLine(Math.min(BOOT_LINES.length - 1, Math.floor((pct / 100) * BOOT_LINES.length)));
      if (pct < 100) {
        raf = requestAnimationFrame(tick);
      } else {
        setTimeout(onDone, 280);
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [onDone, reducedMotion]);

  if (reducedMotion) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        background: COLORS.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 22,
      }}
    >
      <div style={{ position: "relative", width: 68, height: 68, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            border: "2px solid rgba(99,102,241,0.18)",
            borderTopColor: COLORS.indigo,
            animation: "paytrix-spin 1.1s linear infinite",
          }}
        />
        <Bot size={26} color={COLORS.indigo} />
      </div>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 18, color: COLORS.text, marginBottom: 6 }}>
          Paytrix
        </div>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12.5, color: COLORS.textDim, minHeight: 16 }}>
          {BOOT_LINES[line]}…
        </div>
      </div>
      <div style={{ width: 200, height: 3, borderRadius: 2, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
        <div
          style={{
            width: `${progress}%`,
            height: "100%",
            background: `linear-gradient(90deg, ${COLORS.indigo}, ${COLORS.emerald})`,
          }}
        />
      </div>
      <style>{`@keyframes paytrix-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function SettingsPanel({ settings, onChange, onClose }: any) {
  const Row = ({ label, hint, children }: any) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 0", borderBottom: `1px solid ${COLORS.border}` }}>
      <div>
        <div style={{ fontSize: 13.5, color: COLORS.text }}>{label}</div>
        {hint && <div style={{ fontSize: 11.5, color: COLORS.textDim, marginTop: 2 }}>{hint}</div>}
      </div>
      {children}
    </div>
  );

  const Toggle = ({ checked, onClick }: any) => (
    <button
      onClick={onClick}
      style={{
        width: 38,
        height: 22,
        borderRadius: 20,
        border: "none",
        background: checked ? COLORS.indigo : "rgba(255,255,255,0.14)",
        position: "relative",
        cursor: "pointer",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 3,
          left: checked ? 19 : 3,
          width: 16,
          height: 16,
          borderRadius: "50%",
          background: "white",
          transition: "left 0.15s ease",
        }}
      />
    </button>
  );

  const Select = ({ value, options, onChange }: any) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        background: "rgba(255,255,255,0.04)",
        border: `1px solid ${COLORS.border}`,
        color: COLORS.text,
        borderRadius: 8,
        padding: "6px 10px",
        fontSize: 12.5,
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {options.map((o: string) => (
        <option key={o} value={o} style={{ background: COLORS.bg }}>
          {o}
        </option>
      ))}
    </select>
  );

  return (
    <Overlay onBackdropClick={onClose}>
      <div style={{ width: 340 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, margin: 0 }}>Settings</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: COLORS.textDim }}>
            <X size={18} />
          </button>
        </div>
        <Row label="Accent color" hint="Applies to buttons and the checkout card">
          <Select value={settings.accent} options={["Indigo", "Emerald"]} onChange={(v: string) => onChange({ ...settings, accent: v })} />
        </Row>
        <Row label="Reduce motion" hint="Turns off the intro, particles and card tilt">
          <Toggle checked={settings.reducedMotion} onClick={() => onChange({ ...settings, reducedMotion: !settings.reducedMotion })} />
        </Row>
      </div>
    </Overlay>
  );
}

function KernelRings({ activeStep }: { activeStep: number }) {
  return (
    <svg width="120" height="120" viewBox="0 0 120 120">
      {[0, 1, 2].map((i) => (
        <circle
          key={i}
          cx="60"
          cy="60"
          r={26 + i * 16}
          fill="none"
          stroke={i <= activeStep ? COLORS.indigo : "rgba(255,255,255,0.08)"}
          strokeWidth="1.5"
          opacity={i <= activeStep ? 0.9 - i * 0.2 : 0.4}
          style={{ transition: "stroke 0.4s ease, opacity 0.4s ease" }}
        />
      ))}
      <circle cx="60" cy="60" r="10" fill={COLORS.indigo} opacity="0.9" />
    </svg>
  );
}

const CHECK_STEPS = [
  "Authenticating agent identity",
  "Checking idempotency & replay history",
  "Scanning for dark patterns",
  "Running price sentinel & velocity checks",
  "Scoring intent-to-authority alignment",
];

type Stage = "landing" | "check" | "confirming" | "success" | "declined" | "needs_confirmation";

export default function PaytrixLanding() {
  useFonts();

  const [requestText, setRequestText] = useState("order 2 boxes of diabetes care supplies");
  const [touched, setTouched] = useState(false);
  const [amount] = useState(1450);
  const [stage, setStage] = useState<Stage>("landing");
  const [checkStep, setCheckStep] = useState(-1);
  const [showIntro, setShowIntro] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({ accent: "Indigo", reducedMotion: false });
  const [apiResult, setApiResult] = useState<any>(null);
  const [ledgerValid, setLedgerValid] = useState<boolean | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const accentColor = settings.accent === "Emerald" ? COLORS.emerald : COLORS.indigo;
  const requestValid = requestText.trim().length >= 6;

  const buildPayload = (mode: "happy" | "blocked") => ({
    user_id: "usr_demo_123",
    user_prompt: requestText,
    trace_id: `tr_landing_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    intent_envelope: {
      target_price_paise: 150000,
      ceiling_price_paise: 160000,
      min_merchant_trust_score: 0.8,
      required_category: "pharmacy",
      allow_recurring_subscriptions: false,
    },
    proposal: {
      product_id: `MED_LANDING_${Date.now()}`,
      product_name: "Diabetes Care Pack",
      category: "pharmacy",
      price_paise: mode === "blocked" ? 185000 : 145000,
      baseline_price_paise: 145000,
      merchant_trust_score: 0.95,
      product_rating: 4.8,
      has_hidden_subscription: false,
    },
  });

  const runFlow = async (mode: "happy" | "blocked") => {
    setTouched(true);
    if (!requestValid) return;
    setStage("check");
    setCheckStep(0);

    const payload = buildPayload(mode);

    const stepTimer = new Promise<void>((resolve) => {
      let i = 0;
      const tick = () => {
        i++;
        setCheckStep(i);
        if (i < CHECK_STEPS.length - 1) {
          setTimeout(tick, 420);
        } else {
          resolve();
        }
      };
      setTimeout(tick, 420);
    });

    const apiCall = postCheckout(payload);
    const [, result] = await Promise.all([stepTimer, apiCall]);

    setApiResult(result);

    if (result.status === "COMPLETED") {
      const ledger = await getLedger().catch(() => null);
      setLedgerValid(ledger ? ledger.chain_valid : null);
      setStage("success");
    } else if (result.status === "REQUIRE_CONFIRMATION") {
      setStage("needs_confirmation");
    } else {
      setStage("declined");
    }
  };

  const approveConfirmation = async () => {
    if (!apiResult?.trace_id || !apiResult?.confirmation_token) return;
    setStage("confirming");
    setConfirmError(null);
    try {
      const result = await postConfirm(apiResult.trace_id, apiResult.confirmation_token);
      if (result.status === "COMPLETED") {
        setApiResult(result);
        const ledger = await getLedger().catch(() => null);
        setLedgerValid(ledger ? ledger.chain_valid : null);
        setStage("success");
      } else {
        setConfirmError(result.reason || "Confirmation failed");
        setStage("declined");
        setApiResult(result);
      }
    } catch {
      setConfirmError("Could not reach the confirmation endpoint");
      setStage("declined");
    }
  };

  const reset = () => {
    setStage("landing");
    setCheckStep(-1);
    setApiResult(null);
    setLedgerValid(null);
    setConfirmError(null);
  };

  const downloadReceipt = () => {
    const text = `PAYTRIX AUDIT RECEIPT

Trace ID: ${apiResult?.trace_id ?? ""}
Agent request: ${requestText}
Amount: INR ${(apiResult?.amount_paise ?? 0) / 100}
Status: ${apiResult?.status ?? ""}
Gateway ref: ${apiResult?.gateway_ref ?? "n/a"}
Ledger chain valid: ${ledgerValid}
`;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${apiResult?.trace_id ?? "receipt"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (showIntro) {
    return <IntroSplash onDone={() => setShowIntro(false)} reducedMotion={settings.reducedMotion} />;
  }

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "'Inter', sans-serif", position: "relative", overflow: "hidden" }}>
      <ParticleField reducedMotion={settings.reducedMotion} />

      <div
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "22px 48px",
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <ShieldCheck size={20} color={accentColor} />
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 17 }}>Paytrix</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div style={{ fontSize: 13, color: COLORS.textDim, display: "flex", alignItems: "center", gap: 6 }}>
            <Lock size={13} />
            gateway.call_count == 0 until approved
          </div>
          <Link
            href="/dashboard"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12.5,
              color: COLORS.textDim,
              textDecoration: "none",
              border: `1px solid ${COLORS.border}`,
              borderRadius: 9,
              padding: "8px 12px",
            }}
          >
            Failure Lab <ExternalLink size={12} />
          </Link>
          <button
            onClick={() => setSettingsOpen(true)}
            aria-label="Settings"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: `1px solid ${COLORS.border}`,
              borderRadius: 9,
              width: 34,
              height: 34,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: COLORS.textDim,
            }}
          >
            <Settings size={16} />
          </button>
        </div>
      </div>

      <div
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          flexWrap: "wrap-reverse",
          gap: 56,
          alignItems: "center",
          justifyContent: "center",
          padding: "72px 48px 96px",
          maxWidth: 1100,
          margin: "0 auto",
        }}
      >
        <div style={{ maxWidth: 420 }}>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 42, lineHeight: 1.15, margin: "0 0 16px" }}>
            The AI proposes. It never disposes.
          </h1>
          <p style={{ color: COLORS.textDim, fontSize: 15, lineHeight: 1.6, margin: "0 0 32px" }}>
            Every agent request passes through the Safety Kernel &mdash; identity, replay protection, policy,
            risk, and authorization checks &mdash; before a single rupee ever reaches Razorpay.
          </p>

          <label style={{ fontSize: 13, color: COLORS.textDim, display: "block", marginBottom: 6 }}>
            Agent request
          </label>
          <input
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            onBlur={() => setTouched(true)}
            placeholder="order 2 boxes of diabetes care supplies"
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "13px 14px",
              borderRadius: 10,
              background: "rgba(255,255,255,0.04)",
              border: `1px solid ${touched && !requestValid ? COLORS.amber : COLORS.border}`,
              color: COLORS.text,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 14,
              outline: "none",
              marginBottom: 6,
            }}
          />
          <div style={{ minHeight: 18, marginBottom: 14 }}>
            {touched && !requestValid && (
              <span style={{ fontSize: 12.5, color: COLORS.amber, display: "flex", alignItems: "center", gap: 5 }}>
                <AlertTriangle size={13} /> Describe what the agent should buy &mdash; at least a few words.
              </span>
            )}
          </div>

          <button
            onClick={() => runFlow("happy")}
            style={{
              width: "100%",
              padding: "14px 20px",
              borderRadius: 12,
              border: "none",
              background: accentColor,
              color: "white",
              fontSize: 15,
              fontWeight: 600,
              fontFamily: "'Space Grotesk', sans-serif",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              marginBottom: 10,
            }}
          >
            Run agent request <ArrowRight size={16} />
          </button>

          <button
            onClick={() => runFlow("blocked")}
            style={{
              width: "100%",
              padding: "9px",
              borderRadius: 10,
              border: "none",
              background: "transparent",
              color: COLORS.textDim,
              fontSize: 12.5,
              cursor: "pointer",
              textDecoration: "underline",
              textUnderlineOffset: 3,
            }}
          >
            Simulate an over-priced request (blocked)
          </button>
        </div>

        <TiltCard requestText={requestText} amount={amount} accentColor={accentColor} reducedMotion={settings.reducedMotion} />
      </div>

      {stage === "check" && (
        <Overlay>
          <KernelRings activeStep={checkStep} />
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13, color: COLORS.text, marginTop: 18 }}>
            {CHECK_STEPS[Math.min(checkStep, CHECK_STEPS.length - 1)]}…
          </p>
          <div style={{ display: "flex", gap: 6, marginTop: 14 }}>
            {CHECK_STEPS.map((_, i) => (
              <div
                key={i}
                style={{
                  width: 26,
                  height: 3,
                  borderRadius: 2,
                  background: i <= checkStep ? COLORS.indigo : "rgba(255,255,255,0.12)",
                  transition: "background 0.3s ease",
                }}
              />
            ))}
          </div>
        </Overlay>
      )}

      {stage === "needs_confirmation" && (
        <Overlay>
          <div style={{ width: 52, height: 52, borderRadius: "50%", background: "rgba(99,102,241,0.14)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <ShieldCheck size={26} color={COLORS.indigo} />
          </div>
          <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 19, margin: "16px 0 4px" }}>
            Step-up confirmation needed
          </h3>
          <p style={{ fontSize: 13, color: COLORS.textDim, margin: "0 0 6px", textAlign: "center", maxWidth: 300 }}>
            This request scored in the mid-confidence band &mdash; the Safety Kernel wants your explicit approval
            before funds move. No gateway call has happened yet.
          </p>
          {apiResult?.alignment_score != null && (
            <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5, color: COLORS.textDim, margin: "0 0 20px" }}>
              alignment score: {(apiResult.alignment_score * 100).toFixed(1)}%
            </p>
          )}
          <div style={{ display: "flex", gap: 10 }}>
            <PillButton onClick={approveConfirmation} label="Approve & pay" primary />
            <PillButton onClick={reset} label="Cancel" />
          </div>
        </Overlay>
      )}

      {stage === "confirming" && (
        <Overlay>
          <div style={{ width: 34, height: 34, borderRadius: "50%", border: `3px solid ${COLORS.border}`, borderTopColor: COLORS.indigo, animation: "paytrix-spin 0.8s linear infinite" }} />
          <p style={{ fontSize: 13, color: COLORS.textDim, marginTop: 16 }}>Verifying confirmation token &amp; dispatching to Razorpay…</p>
          <style>{`@keyframes paytrix-spin { to { transform: rotate(360deg); } }`}</style>
        </Overlay>
      )}

      {stage === "success" && (
        <Overlay>
          <SuccessCheck />
          <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, margin: "18px 0 4px" }}>
            ₹{((apiResult?.amount_paise ?? 0) / 100).toFixed(2)} authorized
          </h3>
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: COLORS.textDim, margin: "0 0 4px" }}>
            {apiResult?.trace_id}
          </p>
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5, color: COLORS.textDim, margin: "0 0 14px" }}>
            gateway ref {apiResult?.gateway_ref}
          </p>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12,
              color: ledgerValid ? COLORS.emerald : COLORS.amber,
              marginBottom: 20,
            }}
          >
            {ledgerValid ? <Check size={14} /> : <AlertTriangle size={14} />}
            {ledgerValid === null ? "checking chain…" : ledgerValid ? "audit chain VALID" : "chain check inconclusive"}
          </div>
          <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
            <PillButton onClick={downloadReceipt} icon={<Download size={14} />} label="Download receipt" primary />
            <PillButton onClick={reset} label="Done" />
          </div>
        </Overlay>
      )}

      {stage === "declined" && (
        <Overlay>
          <div style={{ width: 52, height: 52, borderRadius: "50%", background: "rgba(245,158,11,0.14)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <X size={26} color={COLORS.amber} />
          </div>
          <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 19, margin: "16px 0 4px" }}>
            Blocked by the Safety Kernel
          </h3>
          <p style={{ fontSize: 13, color: COLORS.textDim, margin: "0 0 6px", textAlign: "center", maxWidth: 300 }}>
            {confirmError || apiResult?.reason || "This request failed policy or risk scoring — Razorpay was never called."}
          </p>
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: COLORS.textDim, margin: "0 0 8px" }}>
            razorpay_called == {String(apiResult?.razorpay_called ?? false)}
          </p>
          {apiResult?.proof_of_non_execution && (
            <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: COLORS.textDim, margin: "0 0 22px", wordBreak: "break-all", maxWidth: 320, textAlign: "center" }}>
              {apiResult.proof_of_non_execution}
            </p>
          )}
          <PillButton onClick={reset} label="Try again" primary />
        </Overlay>
      )}

      {settingsOpen && <SettingsPanel settings={settings} onChange={setSettings} onClose={() => setSettingsOpen(false)} />}
    </div>
  );
}

function Overlay({ children, onBackdropClick }: { children: React.ReactNode; onBackdropClick?: () => void }) {
  return (
    <div
      onClick={onBackdropClick ? (e) => e.target === e.currentTarget && onBackdropClick() : undefined}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10,
        background: "rgba(10,13,20,0.72)",
        backdropFilter: "blur(6px)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        style={{
          background: COLORS.panel,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 20,
          padding: "40px 36px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          backdropFilter: "blur(20px)",
          boxShadow: "0 30px 80px -30px rgba(0,0,0,0.6)",
        }}
      >
        {children}
      </div>
    </div>
  );
}

function PillButton({ label, icon, onClick, primary }: any) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        padding: "10px 18px",
        borderRadius: 10,
        border: primary ? "none" : `1px solid ${COLORS.border}`,
        background: primary ? COLORS.indigo : "transparent",
        color: primary ? "white" : COLORS.textDim,
        fontSize: 13.5,
        fontWeight: 500,
        cursor: "pointer",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {icon} {label}
    </button>
  );
}

function SuccessCheck() {
  return (
    <svg width="56" height="56" viewBox="0 0 56 56">
      <circle cx="28" cy="28" r="26" fill="rgba(16,185,129,0.14)" stroke={COLORS.emerald} strokeWidth="1.5" />
      <path
        d="M18 29 L25 36 L38 21"
        fill="none"
        stroke={COLORS.emerald}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ strokeDasharray: 40, strokeDashoffset: 40, animation: "paytrix-draw 0.5s ease forwards 0.15s" }}
      />
      <style>{`@keyframes paytrix-draw { to { stroke-dashoffset: 0; } }`}</style>
    </svg>
  );
}

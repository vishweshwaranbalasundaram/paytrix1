# PAYTRIX — Security Posture

This document exists so reviewers (and Razorpay hackathon judges) don't have
to reverse-engineer our security model from the code.

## 1. What we store vs. what we never touch

PAYTRIX is a **decision layer in front of** a payment gateway, not a card
vault. We deliberately keep zero cardholder/PAN data in scope:

- We never accept, store, or transmit raw card numbers, CVVs, or UPI PINs.
- The `MockRazorpayGateway` stands in for Razorpay's real hosted
  checkout/tokenization flow — in production, PAYTRIX would call Razorpay's
  APIs and only ever handle Razorpay's opaque `gateway_ref` tokens, never
  raw payment instrument data. This keeps PAYTRIX itself **out of PCI-DSS
  SAQ-D scope** — it only ever sees tokenized references.
- All monetary values are integer paise, never floating point, to avoid
  rounding-based fraud vectors.

## 2. Defense-in-depth layers (in the order a request passes through them)

| # | Layer | What it stops |
|---|-------|----------------|
| 1 | **Agent Identity & Rate Limiting** | Unauthenticated or unregistered AI agents; a single agent hammering the API |
| 2 | **Idempotency / Replay Protection** | Duplicate charges from network retries; tampered replays of a previous `trace_id` |
| 3 | **Anti-Dark-Pattern Interceptor** | Hidden recurring subscriptions the user never consented to |
| 4 | **Price Sentinel** | Dynamic price scalping beyond a baseline tolerance |
| 5 | **Velocity Governor** | Runaway agent spend within a rolling time window |
| 6 | **Intent-to-Authority (I2A) Scoring** | Purchases that don't actually match what the user asked for |
| 7 | **Merchant Reputation Signal** | First-time/unvetted merchants get flagged for extra scrutiny |
| 8 | **Step-Up Confirmation** | Mid-confidence purchases require an explicit signed approval before funds move |
| 9 | **Atomic Wallet Reservation** | Partial/inconsistent balance states from concurrent requests |

Any failure in layers 1–7 halts the request **before** the payment gateway
is ever called, and mints a cryptographic **Proof of Non-Execution (PrNE)**
— an HMAC-SHA256 receipt proving `gateway_call_count == 0` for that trace.

## 3. Sensitive data handling

- `app/policies/sandbox.py` redacts API keys, passwords, and UPI VPA-like
  strings from anything written to `RiskEvent` logs before it ever touches
  disk.
- Agent credentials (`X-Agent-Key`) are stored as SHA-256 hashes
  (`AgentKey.key_hash`), never in plaintext.
- Confirmation tokens and PrNE receipts are HMAC-SHA256 signed with
  server-side secrets (`confirmation_secret`, `prne_secret`) — they cannot
  be forged client-side.

## 4. Known limitations (honest disclosure, not marketing)

- Secrets in `app/core/config.py` are dev-only defaults — a real deployment
  must inject these via environment variables / a secrets manager, never
  commit them.
- The demo agent key (`demo_agent_key`) is intentionally public in this
  repo for hackathon demo purposes only. Production agent onboarding would
  issue keys out-of-band and never ship a default.
- Rate limiting and idempotency are enforced at the application/DB layer,
  not at a network edge (no WAF/CDN layer in this demo).

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PAYTRIX — Autonomous Micro-Mandate Guardrails",
  description: "Agentic commerce safety kernel and micro-mandate payment mesh.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

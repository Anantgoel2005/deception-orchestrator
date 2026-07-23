"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function DemoPage() {
  const [running, setRunning] = useState(false); const [message, setMessage] = useState(""); const router = useRouter();
  async function run() { setRunning(true); setMessage(""); try { const result = await api.demo.run(); setMessage(`${result.events_created} simulated events created. Opening the investigation…`); setTimeout(() => router.push(`/investigations/${result.session_id}`), 650); } catch { setMessage("Scenario failed. Confirm the API and database are healthy."); } finally { setRunning(false); } }
  return <div className="max-w-2xl space-y-6"><div><h2 className="text-2xl font-bold">Demo Lab</h2><p className="text-sm text-muted-foreground">Safe, deterministic attack simulations for a reliable presentation.</p></div><section className="rounded-xl border border-primary/30 bg-card p-6"><p className="text-xs font-semibold tracking-widest text-primary">CREDENTIAL TO EXFILTRATION</p><h3 className="mt-2 text-xl font-semibold">SSH and HTTP attack chain</h3><p className="mt-2 text-sm text-muted-foreground">Creates credential probing, a successful access, command activity, an HTTP exploit attempt, and a canary callback using TEST-NET addresses.</p><button onClick={run} disabled={running} className="mt-5 rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{running ? "Running scenario…" : "Run safe scenario"}</button>{message && <p className="mt-4 text-sm text-emerald-400">{message}</p>}</section></div>;
}

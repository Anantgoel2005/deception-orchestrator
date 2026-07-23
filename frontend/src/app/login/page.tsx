"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter(); const [username, setUsername] = useState("admin"); const [password, setPassword] = useState(""); const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setError("");
    try { await api.auth.login(username, password); router.replace("/"); } catch { setError("Invalid credentials or server configuration."); }
  }
  return <main className="min-h-screen grid place-items-center bg-background p-6"><form onSubmit={submit} className="w-full max-w-sm rounded-xl border border-border bg-card p-7 space-y-5 shadow-2xl"><div><p className="text-primary text-xs font-bold tracking-[0.24em]">DECEPTION</p><h1 className="text-2xl font-bold mt-1">Analyst Console</h1><p className="text-sm text-muted-foreground mt-2">Sign in to the protected control plane.</p></div><label className="block text-sm">Username<input value={username} onChange={(e) => setUsername(e.target.value)} className="mt-1 w-full rounded border border-border bg-background p-2" /></label><label className="block text-sm">Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 w-full rounded border border-border bg-background p-2" /></label>{error && <p className="text-sm text-red-400">{error}</p>}<button className="w-full rounded bg-primary p-2 text-sm font-medium text-primary-foreground">Sign in</button></form></main>;
}

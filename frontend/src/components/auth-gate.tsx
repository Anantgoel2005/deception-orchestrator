"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname(); const router = useRouter(); const [ready, setReady] = useState(pathname === "/login");
  useEffect(() => { if (pathname === "/login") { setReady(true); return; } api.auth.me().then(() => setReady(true)).catch(() => router.replace("/login")); }, [pathname, router]);
  if (!ready) return <main className="min-h-screen grid place-items-center text-sm text-muted-foreground">Checking secure session…</main>;
  if (pathname === "/login") return <>{children}</>;
  const links = [["/", "Dashboard"], ["/events", "Events"], ["/alerts", "Alerts"], ["/honeypots", "Local Decoys"], ["/canaries", "Canaries"], ["/demo", "Demo Lab"], ["/settings", "Settings"]];
  return <div className="flex h-screen"><aside className="w-56 border-r border-border bg-card flex flex-col p-4 shrink-0"><div className="mb-6 px-2"><h1 className="text-sm font-bold tracking-widest text-primary uppercase">Deception</h1><p className="text-[10px] text-muted-foreground tracking-wide">Orchestrator</p></div><nav className="flex flex-col gap-1">{links.map(([href, label]) => <Link key={href} href={href} className="rounded px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground">{label}</Link>)}</nav><p className="mt-auto text-xs text-emerald-400">● Protected session</p></aside><main className="flex-1 overflow-auto p-6">{children}</main></div>;
}

import type { Metadata } from "next";
import "./globals.css";
import { AuthGate } from "@/components/auth-gate";

export const metadata: Metadata = {
  title: "Deception Orchestrator",
  description: "Secure deception operations console for SOC analysts",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" className="dark"><body className="bg-background text-foreground antialiased"><AuthGate>{children}</AuthGate></body></html>;
}

"use client";

import { useEffect, useState } from "react";
import { api, type Canary } from "@/lib/api";

export default function CanariesPage() {
  const [canaries, setCanaries] = useState<Canary[]>([]);
  const [genType] = useState("url");
  const [genCount, setGenCount] = useState(5);
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.canaries.list({ limit: "200" }).then((r) => {
      setCanaries(r.items);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const generate = async () => {
    setLoading(true);
    try {
      await api.canaries.generate({
        canary_type: "url",
        count: genCount,
        planted_location: location || undefined,
      });
      setLocation("");
    } catch {
    }
    load();
  };

  const copyToken = (value: string) => {
    navigator.clipboard.writeText(value);
  };

  const remove = async (id: string) => {
    try {
      await api.canaries.delete(id);
    } catch {
    }
    load();
  };

  const statusBadge = (s: string) => {
    switch (s) {
      case "active":
        return "bg-emerald-500/10 text-emerald-400";
      case "tripped":
        return "bg-red-500/10 text-red-400";
      case "revoked":
        return "bg-muted text-muted-foreground";
      case "expired":
        return "bg-amber-500/10 text-amber-400";
      default:
        return "";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Canary Tokens</h2>
        <p className="text-sm text-muted-foreground">
          Generate honeytokens that alert on interaction
        </p>
      </div>

      <div className="bg-card border border-border rounded-lg p-4 flex gap-3 items-end flex-wrap">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Type</label>
          <select
            value={genType}
            className="bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary"
          >
            <option value="url">URL</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Count</label>
          <input
            type="number"
            value={genCount}
            onChange={(e) => setGenCount(Number(e.target.value))}
            min={1}
            max={100}
            className="w-20 bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-muted-foreground block mb-1">
            Planted Location
          </label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="/var/www/.env"
            className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary"
          />
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          Generate
        </button>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="overflow-auto max-h-[600px]">
            <table className="w-full text-sm">
              <thead className="bg-accent/50 sticky top-0">
                <tr>
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium uppercase">
                    Token
                  </th>
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium uppercase">
                    Type
                  </th>
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium uppercase">
                    Status
                  </th>
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium uppercase">
                    Location
                  </th>
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium uppercase">
                    Tripped
                  </th>
                  <th className="text-right px-4 py-2 text-xs text-muted-foreground font-medium uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {canaries.map((c) => (
                  <tr key={c.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-2 font-mono text-xs max-w-[280px] truncate" title={c.token_value}>
                      {c.token_value}
                    </td>
                    <td className="px-4 py-2">
                      <span className="text-[10px] uppercase bg-accent px-2 py-0.5 rounded">
                        {c.canary_type}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-medium ${statusBadge(c.status)}`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground max-w-[150px] truncate">
                      {c.planted_location || "—"}
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground font-mono">
                      {c.trip_source_ip || "—"}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => copyToken(c.callback_url || c.token_value)}
                          className="text-xs text-sky-400 hover:text-sky-300"
                          title="Copy token"
                        >
                          Copy
                        </button>
                        <button
                          onClick={() => remove(c.id)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          Revoke
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {canaries.length === 0 && (
            <div className="text-center text-muted-foreground py-12 text-sm">
              No canary tokens generated yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

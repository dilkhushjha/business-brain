"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "11111111-1111-1111-1111-111111111111";

type SyncStatus = {
  status?: string;
  name?: string;
  version?: string;
  last_seen_at?: string;
  last_sync_at?: string;
  last_success_at?: string;
  last_error?: string | null;
};

type ImportRun = { completed_at?: string; started_at?: string; file_name?: string };

function formatTime(value?: string) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("en-IN", {
    day: "numeric", month: "short", hour: "numeric", minute: "2-digit"
  });
}

export default function DataFreshness() {
  const [sync, setSync] = useState<SyncStatus | null>(null);
  const [latest, setLatest] = useState<ImportRun | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch(`${API}/connectors/status/${ID}`).then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/imports/${ID}/history?limit=1`).then((r) => r.ok ? r.json() : []).catch(() => []),
    ]).then(([status, history]) => {
      if (cancelled) return;
      setSync(status);
      if (history?.[0]) setLatest(history[0]);
    });
    return () => { cancelled = true; };
  }, []);

  const lastSync = sync?.last_success_at || latest?.completed_at || latest?.started_at;
  const connected = sync?.status === "connected" || sync?.status === "active";
  const failed = Boolean(sync?.last_error) && !connected;

  return (
    <div className={`freshnessCard ${connected ? "isConnected" : failed ? "hasError" : ""}`}>
      <div className="freshnessStatus">
        <span className="freshnessDot" />
        <span>{connected ? "Data connection active" : failed ? "Data connection needs attention" : "Data connection not configured"}</span>
      </div>
      <div className="freshnessDetails">
        <span>Last synced <strong>{formatTime(lastSync)}</strong></span>
        {latest?.file_name ? <span>Source <strong>{latest.file_name}</strong></span> : null}
        {sync?.last_error ? <span className="freshnessError">{sync.last_error}</span> : null}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { apiFetch, getBusinessId } from "../lib/api";



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

export default function DataFreshness({ businessName }: { businessName: string }) {
  const [sync, setSync] = useState<SyncStatus | null>(null);
  const [latest, setLatest] = useState<ImportRun | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch(`/connectors/status/${getBusinessId()}`).then((r) => r.ok ? r.json() : null).catch(() => null),
      apiFetch(`/imports/${getBusinessId()}/history?limit=1`).then((r) => r.ok ? r.json() : []).catch(() => []),
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
    <div className={`freshnessInline ${connected ? "isConnected" : failed ? "hasError" : ""}`}>
      <span className="freshnessDot" />
      <strong>{businessName}</strong>
      <span className="freshnessSeparator">·</span>
      <span>Last synced {formatTime(lastSync)}</span>
      {latest?.file_name ? <><span className="freshnessSeparator">·</span><span>{latest.file_name}</span></> : null}
    </div>
  );
}

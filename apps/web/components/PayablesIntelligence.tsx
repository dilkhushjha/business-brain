"use client";

import { useEffect, useState } from "react";
import { apiFetch, getBusinessId, ApiAuthError } from "../lib/api";

type PayablesSummary = {
  outstanding: number;
  overdue: number;
  overdue_pct: number;
};

const money = (value: number) => {
  if (!Number.isFinite(value)) return "—";
  if (Math.abs(value) >= 10000000) return `₹${(value / 10000000).toFixed(2)}Cr`;
  if (Math.abs(value) >= 100000) return `₹${(value / 100000).toFixed(2)}L`;
  if (Math.abs(value) >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
};

export default function PayablesIntelligence() {
  const [summary, setSummary] = useState<PayablesSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const businessId = getBusinessId();
    if (!businessId) return;
    apiFetch(`/payables/${businessId}/summary`)
      .then((response) => {
        if (!response.ok) throw new Error(`Payables service returned ${response.status}`);
        return response.json();
      })
      .then(setSummary)
      .catch((err) => {
        if (err instanceof ApiAuthError) return;
        setError(err instanceof Error ? err.message : "Unable to load payables.");
      });
  }, []);

  const outstanding = summary?.outstanding ?? 0;
  const overdue = summary?.overdue ?? 0;
  const notDue = Math.max(outstanding - overdue, 0);

  return <section className="card">
    <div className="sectionHeading"><span>PAYABLES</span><small>Business-level supplier invoice position</small></div>
    {error ? <div className="errorBox">{error}</div> : <div className="receivableSummary">
      <div className="receivablePrimary"><span>Outstanding</span><strong>{summary ? money(outstanding) : "—"}</strong><small>unpaid purchase invoice value</small></div>
      <div className="receivableBreakdown">
        <div><span>Not overdue</span><strong>{summary ? money(notDue) : "—"}</strong></div>
        <div><span>Overdue</span><strong>{summary ? money(overdue) : "—"}</strong></div>
      </div>
      <div className="receivableMeta"><span>Overdue share</span><b>{summary ? `${summary.overdue_pct.toFixed(0)}%` : "—"}</b><small>Outstanding = unpaid supplier invoice value</small></div>
    </div>}
  </section>;
}

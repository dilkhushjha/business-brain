"use client";

import { useEffect, useState } from "react";
import Icon from "./Icons";
import { ApiAuthError, apiFetch, clearSession, getBusinessId } from "../lib/api";

type Audit = {
  status?: string;
  summary?: Record<string, number>;
  issue_count?: number;
};

type AuditCard = {
  key: "data" | "inventory" | "financial";
  label: string;
  title: string;
  description: string;
  endpoint: string;
};

const audits: AuditCard[] = [
  { key: "data", label: "DATA QUALITY", title: "Imported data", description: "Entity ambiguity, missing document identity, invalid values and document totals.", endpoint: "/data-integrity" },
  { key: "inventory", label: "INVENTORY", title: "Inventory ledger", description: "Purchase/sale movement reconciliation, orphan movements and negative balances.", endpoint: "/inventory" },
  { key: "financial", label: "FINANCIAL LINKAGE", title: "Payments & documents", description: "Document paid amounts compared with linked payment ledger entries and unlinked payments.", endpoint: "/financial-integrity" },
];

const issueCount = (audit: Audit | null) => {
  if (!audit) return null;
  if (typeof audit.issue_count === "number") return audit.issue_count;
  return Object.values(audit.summary || {}).reduce((sum, value) => sum + Number(value || 0), 0);
};

export default function DataIntegrityCenter({ dataVersion = 0 }: { dataVersion?: number }) {
  const [results, setResults] = useState<Record<string, Audit | null>>({ data: null, inventory: null, financial: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const businessId = getBusinessId();
    if (!businessId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");

    Promise.all(audits.map(async (audit) => {
      const path = audit.key === "inventory"
        ? audit.endpoint + "/" + businessId + "?limit=50"
        : audit.endpoint + "/" + businessId;
      const response = await apiFetch(path);
      if (response.status === 401) throw new ApiAuthError("Authentication required");
      if (!response.ok) throw new Error(audit.title + " audit returned " + response.status);
      return [audit.key, await response.json()] as const;
    }))
      .then((entries) => setResults(Object.fromEntries(entries)))
      .catch((err) => {
        if (err instanceof ApiAuthError) {
          clearSession();
          return;
        }
        setError(err instanceof Error ? err.message : "Unable to load data integrity audits.");
      })
      .finally(() => setLoading(false));
  }, [dataVersion]);

  const cards = audits.map((audit) => ({ ...audit, result: results[audit.key], issues: issueCount(results[audit.key]) }));
  const totalIssues = cards.reduce((sum, card) => sum + (card.issues ?? 0), 0);
  const attention = cards.filter((card) => card.result?.status === "attention_required").length;

  return (
    <section className="integrityCenter">
      <div className="integrityHero">
        <div>
          <span className="eyebrow">DATA INTEGRITY</span>
          <h2>Can Business Brain trust the data?</h2>
          <p>Read-only checks that surface reconciliation and data-quality exceptions before they affect business conclusions.</p>
        </div>
        <div className={"integrityHealth " + (attention ? "needsAttention" : "clear")}>
          <strong>{loading ? "…" : attention ? attention : "✓"}</strong>
          <span>{loading ? "checking audits" : attention ? "audit(s) need review" : "all audits reconciled"}</span>
        </div>
      </div>

      {error && <div className="integrityError"><Icon name="alert" className="icon" /><span>{error}</span></div>}

      <div className="integritySummary">
        <div><b>{loading ? "…" : totalIssues}</b><span>Detected issues</span></div>
        <div><b>{loading ? "…" : attention}</b><span>Require attention</span></div>
        <div><b>{cards.length}</b><span>Integrity domains</span></div>
        <div className="integritySummaryNote"><span>Principle</span><b>No silent repair or guessing</b></div>
      </div>

      <div className="integrityGrid">
        {cards.map((card) => {
          const reconciled = card.result?.status === "reconciled";
          return (
            <article className="integrityCard" key={card.key}>
              <div className="integrityCardHead">
                <div><span className="eyebrow">{card.label}</span><h3>{card.title}</h3></div>
                <span className={"integrityStatus " + (loading && !card.result ? "loading" : reconciled ? "ok" : "attention")}>
                  {loading && !card.result ? "Checking" : reconciled ? "Reconciled" : "Attention"}
                </span>
              </div>
              <p>{card.description}</p>
              <div className="integrityMetric"><strong>{loading && !card.result ? "…" : card.issues ?? 0}</strong><span>issue{card.issues === 1 ? "" : "s"} detected</span></div>
              {card.result?.summary && (
                <div className="integrityDetails">
                  {Object.entries(card.result.summary).slice(0, 4).map(([key, value]) => (
                    <div key={key}><span>{key.replaceAll("_", " ")}</span><b>{String(value)}</b></div>
                  ))}
                </div>
              )}
              <small className="integrityReadOnly">Read-only audit · source data unchanged</small>
            </article>
          );
        })}
      </div>

      <div className="integrityPrinciples">
        <div><Icon name="check" className="icon" /><div><b>Reconcile</b><span>Compare canonical documents, ledgers and derived state.</span></div></div>
        <div><Icon name="alert" className="icon" /><div><b>Surface</b><span>Show exceptions explicitly instead of hiding them in downstream metrics.</span></div></div>
        <div><Icon name="pulse" className="icon" /><div><b>Protect reasoning</b><span>Degrade to uncertainty when business evidence is incomplete.</span></div></div>
      </div>
    </section>
  );
}

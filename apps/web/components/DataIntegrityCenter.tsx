"use client";

import { useEffect, useState } from "react";
import Icon from "./Icons";
import { ApiAuthError, apiFetch, clearSession, getBusinessId } from "../lib/api";

type Audit = {
  status?: string;
  summary?: Record<string, number>;
  issue_count?: number;
};

type Readiness = {
  status?: "ready" | "ready_with_warnings" | "not_ready";
  counts?: Record<string, number>;
  blockers?: string[];
  warnings?: string[];
  checks?: Array<{ code?: string; status?: string; message?: string }>;
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
  const [readiness, setReadiness] = useState<Readiness | null>(null);

  useEffect(() => {
    const businessId = getBusinessId();
    if (!businessId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");

    Promise.all([
      ...audits.map(async (audit) => {
      const path = audit.key === "inventory"
        ? audit.endpoint + "/" + businessId + "?limit=50"
        : audit.endpoint + "/" + businessId;
      const response = await apiFetch(path);
      if (response.status === 401) throw new ApiAuthError("Authentication required");
      if (!response.ok) throw new Error(audit.title + " audit returned " + response.status);
      return [audit.key, await response.json()] as const;
      }),
      (async () => {
        const response = await apiFetch("/pilot/" + businessId + "/readiness");
        if (response.status === 401) throw new ApiAuthError("Authentication required");
        if (!response.ok) throw new Error("Pilot readiness returned " + response.status);
        return await response.json() as Readiness;
      })(),
    ])
      .then((entries) => {
        const auditEntries = entries.slice(0, audits.length) as Array<readonly [string, Audit]>;
        setResults(Object.fromEntries(auditEntries));
        setReadiness(entries[audits.length] as Readiness);
      })
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

      {readiness && <section className={"pilotReadiness " + (readiness.status === "not_ready" ? "blocked" : readiness.status === "ready_with_warnings" ? "warning" : "ready")}>
        <div className="pilotReadinessHead">
          <div><span className="eyebrow">PILOT READINESS</span><h3>{readiness.status === "ready" ? "Ready for a real-business pilot" : readiness.status === "ready_with_warnings" ? "Pilot-ready with limitations" : "Not ready for a real-business pilot"}</h3><p>Sales data, supporting masters and integrity checks are evaluated before Business Brain is trusted with live SME decisions.</p></div>
          <strong>{readiness.status === "ready" ? "READY" : readiness.status === "ready_with_warnings" ? "REVIEW" : "BLOCKED"}</strong>
        </div>
        <div className="pilotReadinessStats">
          <span><b>{readiness.counts?.sales ?? 0}</b> sales</span>
          <span><b>{readiness.counts?.purchases ?? 0}</b> purchases</span>
          <span><b>{readiness.counts?.customers ?? 0}</b> customers</span>
          <span><b>{readiness.counts?.products ?? 0}</b> products</span>
          {Boolean(readiness.blockers?.length) && <span><b>{readiness.blockers?.length}</b> blockers</span>}
          {Boolean(readiness.warnings?.length) && <span><b>{readiness.warnings?.length}</b> warnings</span>}
        </div>
        {(readiness.blockers?.length || readiness.warnings?.length) ? <div className="pilotReadinessChecks">{(readiness.checks || []).filter((check) => check.status !== "pass").slice(0, 4).map((check) => <div key={check.code}><b>{String(check.code || "CHECK").replaceAll("_", " ")}</b><span>{check.message}</span></div>)}</div> : <small>All pilot gate checks currently pass.</small>}
      </section>}

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

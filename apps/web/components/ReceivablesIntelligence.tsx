"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";
import type { ReasoningPayload } from "../lib/reasoning";

const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
type S = { outstanding: number; overdue: number; overdue_pct: number; buckets: Record<string, number> };
type C = { name: string; overdue_amount: number; days_overdue: number };

export default function ReceivablesIntelligence({ onExplain }: { onExplain?: (reasoning: ReasoningPayload) => void }) {
  const [s, setS] = useState<S | null>(null);
  const [c, setC] = useState<C[]>([]);
  useEffect(() => {
    Promise.all([
      apiFetch(`/receivables/${getBusinessId()}/summary`).then((r) => (r.ok ? r.json() : null)),
      apiFetch(`/receivables/${getBusinessId()}/overdue?limit=5`).then((r) => (r.ok ? r.json() : [])),
    ]).then(([a, b]) => { setS(a); setC(b); }).catch(() => {});
  }, []);
  if (!s || !s.outstanding) return null;

  const reasoning: ReasoningPayload = {
    title: "Receivables & cash",
    value: money(s.outstanding),
    change: `${s.overdue_pct}% overdue`,
    context: "Outstanding invoice balances are based on recorded receivables; overdue amounts are invoices past their recorded due date.",
    why: "This separates money already earned from money actually collected. A rising overdue balance can put pressure on cash even when sales look healthy.",
    implication: s.overdue > 0 ? `${money(s.overdue)} is overdue, so collection timing deserves attention.` : "Receivables visibility helps protect cash flow and collection discipline.",
    evidence: [
      { label: "Outstanding", value: money(s.outstanding) },
      { label: "Overdue", value: money(s.overdue) },
      { label: "Overdue share", value: `${s.overdue_pct}%` },
      ...(c.length ? [{ label: "Customers needing collection", value: `${c.length}`, detail: "Highest overdue balances returned by the receivables analysis" }] : []),
    ],
  };
  const explain = () => onExplain?.(reasoning);
  return (
    <section className={`card ${onExplain ? "reasoningClickable" : ""}`} onClick={onExplain ? explain : undefined} onKeyDown={onExplain ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); explain(); } } : undefined} role={onExplain ? "button" : undefined} tabIndex={onExplain ? 0 : undefined}>
      <div className="cardTitle"><span><Icon name="clock" className="icon" /></span><h3>Receivables &amp; cash</h3><small>Outstanding invoices</small></div>
      <div className="marginStats">
        <div><span>Outstanding</span><b>{money(s.outstanding)}</b></div>
        <div><span>Overdue</span><b className={s.overdue > 0 ? "negative" : undefined}>{money(s.overdue)}</b></div>
        <div><span>Overdue share</span><b>{s.overdue_pct}%</b></div>
      </div>
      {c.length > 0 && <div className="marginAlerts"><strong>Customers needing collection</strong>{c.map((x) => <div className="marginRow" key={x.name}><span>{x.name}</span><b>{money(x.overdue_amount)}</b><em>{x.days_overdue} days overdue</em></div>)}</div>}
    </section>
  );
}

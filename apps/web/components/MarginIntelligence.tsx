"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";
import type { ReasoningPayload } from "../lib/reasoning";

type Summary = { revenue: number; cost: number; gross_profit: number; gross_margin_pct: number | null; cost_coverage_pct: number };
type Product = { name: string; revenue: number; gross_profit: number; margin_pct: number; severity: string };
const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function MarginIntelligence({ onExplain }: { onExplain?: (reasoning: ReasoningPayload) => void }) {
  const [s, setS] = useState<Summary | null>(null);
  const [p, setP] = useState<Product[]>([]);
  useEffect(() => {
    Promise.all([
      apiFetch(`/margin/${getBusinessId()}/summary?days=30`).then((r) => (r.ok ? r.json() : null)),
      apiFetch(`/margin/${getBusinessId()}/low-margin?days=30&threshold=10&limit=5`).then((r) => (r.ok ? r.json() : [])),
    ]).then(([a, b]) => { setS(a); setP(b); }).catch(() => {});
  }, []);
  if (!s) return null;

  const reasoning: ReasoningPayload = {
    title: "Profit & margin",
    value: s.gross_margin_pct == null ? "—" : `${s.gross_margin_pct}%`,
    change: "Last 30 days",
    context: "Gross margin is calculated from recorded revenue and cost for the current 30-day window.",
    why: "This shows how much of recent revenue remains after recorded product cost. Low-margin products can make revenue growth less valuable.",
    implication: p.length ? `${p.length} products are below the 10% margin review threshold and may be diluting profitability.` : "Healthy margin visibility helps distinguish revenue growth from profitable growth.",
    evidence: [
      { label: "Revenue", value: money(s.revenue) },
      { label: "Recorded cost", value: money(s.cost) },
      { label: "Gross profit", value: money(s.gross_profit) },
      ...(p.length ? [{ label: "Low-margin products", value: `${p.length}`, detail: "Below the 10% review threshold" }] : []),
    ],
  };
  const explain = () => onExplain?.(reasoning);
  return (
    <section className={`card ${onExplain ? "reasoningClickable" : ""}`} onClick={onExplain ? explain : undefined} onKeyDown={onExplain ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); explain(); } } : undefined} role={onExplain ? "button" : undefined} tabIndex={onExplain ? 0 : undefined}>
      <div className="cardTitle"><span><Icon name="percent" className="icon" /></span><h3>Profit &amp; margin</h3><small>Last 30 days</small></div>
      <div className="marginStats">
        <div><span>Gross profit</span><b>{money(s.gross_profit)}</b></div>
        <div><span>Gross margin</span><b>{s.gross_margin_pct == null ? "—" : `${s.gross_margin_pct}%`}</b></div>
        <div><span>Revenue covered</span><b>{s.cost_coverage_pct}%</b></div>
      </div>
      {p.length > 0 && <div className="marginAlerts"><strong>Low-margin products</strong>{p.map((x) => <div className="marginRow" key={x.name}><span>{x.name}</span><b className="negative">{x.margin_pct.toFixed(1)}%</b><em>{money(x.revenue)} revenue</em></div>)}</div>}
    </section>
  );
}

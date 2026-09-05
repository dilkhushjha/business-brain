"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";



type Summary = { revenue: number; cost: number; gross_profit: number; gross_margin_pct: number | null; cost_coverage_pct: number };
type Product = { name: string; revenue: number; gross_profit: number; margin_pct: number; severity: string };

const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function MarginIntelligence() {
  const [s, setS] = useState<Summary | null>(null);
  const [p, setP] = useState<Product[]>([]);

  useEffect(() => {
    Promise.all([
      apiFetch(`/margin/${getBusinessId()}/summary?days=30`).then((r) => (r.ok ? r.json() : null)),
      apiFetch(`/margin/${getBusinessId()}/low-margin?days=30&threshold=10&limit=5`).then((r) => (r.ok ? r.json() : [])),
    ]).then(([a, b]) => { setS(a); setP(b); }).catch(() => {});
  }, []);

  if (!s) return null;

  return (
    <section className="card">
      <div className="cardTitle">
        <span><Icon name="percent" className="icon" /></span>
        <h3>Profit &amp; margin</h3>
        <small>Last 30 days</small>
      </div>
      <div className="marginStats">
        <div><span>Gross profit</span><b>{money(s.gross_profit)}</b></div>
        <div><span>Gross margin</span><b>{s.gross_margin_pct == null ? "—" : `${s.gross_margin_pct}%`}</b></div>
        <div><span>Revenue covered</span><b>{s.cost_coverage_pct}%</b></div>
      </div>
      {p.length > 0 && (
        <div className="marginAlerts">
          <strong>Low-margin products</strong>
          {p.map((x) => (
            <div className="marginRow" key={x.name}>
              <span>{x.name}</span>
              <b className="negative">{x.margin_pct.toFixed(1)}%</b>
              <em>{money(x.revenue)} revenue</em>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
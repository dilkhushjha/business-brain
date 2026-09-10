"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";
import type { ReasoningPayload } from "../lib/reasoning";

const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
type Row = { name: string; units_sold: number; revenue: number; avg_daily_units: number; signal: string; recommended_review?: string | null };

export default function InventoryIntelligence({ onExplain }: { onExplain?: (reasoning: ReasoningPayload) => void }) {
  const [r, setR] = useState<Row[]>([]);
  useEffect(() => { apiFetch(`/inventory/${getBusinessId()}/signals?days=30&limit=5`).then((x) => (x.ok ? x.json() : [])).then(setR).catch(() => {}); }, []);
  if (!r.length) return null;

  const fast = r.filter((x) => x.signal === "fast_mover");
  const reasoning: ReasoningPayload = {
    title: "Inventory signals",
    value: `${fast.length} fast mover${fast.length === 1 ? "" : "s"}`,
    change: "Last 30 days",
    context: "This view currently uses recent sales velocity, not a real-time stock-on-hand balance.",
    why: "Products with sustained sales velocity may need closer stock review. This is a demand signal rather than proof that inventory is low.",
    implication: fast.length ? `${fast.length} product${fast.length === 1 ? " is" : "s are"} moving faster than the normal threshold and may deserve a stock check.` : "Sales velocity provides an early indicator for where inventory deserves attention.",
    evidence: r.map((x) => ({ label: x.name, value: `${x.avg_daily_units.toFixed(1)}/day`, detail: `${x.units_sold} units sold · ${money(x.revenue)} revenue · ${x.signal.replaceAll("_", " ")}` })),
  };
  const explain = () => onExplain?.(reasoning);
  return (
    <section className={`card ${onExplain ? "reasoningClickable" : ""}`} onClick={onExplain ? explain : undefined} onKeyDown={onExplain ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); explain(); } } : undefined} role={onExplain ? "button" : undefined} tabIndex={onExplain ? 0 : undefined}>
      <div className="cardTitle"><span><Icon name="box" className="icon" /></span><h3>Inventory signals</h3><small>Based on recent sales velocity</small></div>
      <div className="marginAlerts">{r.map((x) => <div className="marginRow" key={x.name}><span>{x.name}</span><b>{x.avg_daily_units.toFixed(1)}/day</b><em>{x.signal === "fast_mover" ? <span className="tag good">FAST MOVER</span> : <span className="tag">NORMAL</span>} · {money(x.revenue)}</em></div>)}</div>
    </section>
  );
}

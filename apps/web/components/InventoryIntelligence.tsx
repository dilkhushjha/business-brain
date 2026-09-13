"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";
import type { ReasoningPayload } from "../lib/reasoning";

const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
type VelocityRow = { name: string; units_sold: number; revenue: number; avg_daily_units: number; signal: string; recommended_review?: string | null };
type StockRiskRow = { name: string; quantity_on_hand: number; avg_daily_units: number; days_of_cover: number; snapshot_date: string; severity: string };
type StockRisk = { stockout_risk: StockRiskRow[]; excess_inventory: StockRiskRow[] };

export default function InventoryIntelligence({ onExplain }: { onExplain?: (reasoning: ReasoningPayload) => void }) {
  const [velocity, setVelocity] = useState<VelocityRow[]>([]);
  const [stockRisk, setStockRisk] = useState<StockRisk | null>(null);

  useEffect(() => {
    apiFetch(`/inventory/${getBusinessId()}/signals?days=30&limit=5`).then((x) => (x.ok ? x.json() : [])).then(setVelocity).catch(() => {});
    apiFetch(`/inventory/${getBusinessId()}/stock-risk?limit=5`).then((x) => (x.ok ? x.json() : null)).then(setStockRisk).catch(() => {});
  }, []);

  const hasStockRisk = !!stockRisk && (stockRisk.stockout_risk.length > 0 || stockRisk.excess_inventory.length > 0);
  if (!velocity.length && !hasStockRisk) return null;

  if (hasStockRisk && stockRisk) {
    const { stockout_risk, excess_inventory } = stockRisk;
    const reasoning: ReasoningPayload = {
      title: "Inventory signals",
      value: `${stockout_risk.length} at risk of stockout`,
      change: `${excess_inventory.length} with excess stock`,
      context: "Based on your actual stock-on-hand levels compared to recent sales velocity, not just a sales-volume proxy.",
      why: "Days of cover = current stock / average daily units sold. Low days of cover risks running out; very high days of cover ties up capital in stock that isn't moving.",
      implication: stockout_risk.length
        ? `${stockout_risk[0].name} has only about ${stockout_risk[0].days_of_cover.toFixed(0)} day(s) of cover left at current sales pace.`
        : excess_inventory.length
        ? `${excess_inventory[0].name} has roughly ${excess_inventory[0].days_of_cover.toFixed(0)} days of cover -- far more than it's currently selling through.`
        : "Stock levels look healthy relative to recent sales velocity.",
      evidence: [
        ...stockout_risk.map((x) => ({ label: x.name, value: `${x.days_of_cover.toFixed(0)}d cover`, detail: `${x.quantity_on_hand} on hand · ${x.avg_daily_units}/day · stockout risk` })),
        ...excess_inventory.map((x) => ({ label: x.name, value: `${x.days_of_cover.toFixed(0)}d cover`, detail: `${x.quantity_on_hand} on hand · ${x.avg_daily_units}/day · excess stock` })),
      ],
    };
    const explain = () => onExplain?.(reasoning);
    return (
      <section className={`card ${onExplain ? "reasoningClickable" : ""}`} onClick={onExplain ? explain : undefined} onKeyDown={onExplain ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); explain(); } } : undefined} role={onExplain ? "button" : undefined} tabIndex={onExplain ? 0 : undefined}>
        <div className="cardTitle"><span><Icon name="box" className="icon" /></span><h3>Inventory signals</h3><small>Based on actual stock levels</small></div>
        <div className="marginAlerts">
          {stockout_risk.map((x) => <div className="marginRow" key={`out-${x.name}`}><span>{x.name}</span><b>{x.days_of_cover.toFixed(0)}d cover</b><em><span className="tag danger">STOCKOUT RISK</span> · {x.quantity_on_hand} on hand</em></div>)}
          {excess_inventory.map((x) => <div className="marginRow" key={`excess-${x.name}`}><span>{x.name}</span><b>{x.days_of_cover.toFixed(0)}d cover</b><em><span className="tag warning">EXCESS STOCK</span> · {x.quantity_on_hand} on hand</em></div>)}
        </div>
      </section>
    );
  }

  const fast = velocity.filter((x) => x.signal === "fast_mover");
  const reasoning: ReasoningPayload = {
    title: "Inventory signals",
    value: `${fast.length} fast mover${fast.length === 1 ? "" : "s"}`,
    change: "Last 30 days",
    context: "This view currently uses recent sales velocity, not a real-time stock-on-hand balance -- import a stock summary to see actual stockout/excess risk instead.",
    why: "Products with sustained sales velocity may need closer stock review. This is a demand signal rather than proof that inventory is low.",
    implication: fast.length ? `${fast.length} product${fast.length === 1 ? " is" : "s are"} moving faster than the normal threshold and may deserve a stock check.` : "Sales velocity provides an early indicator for where inventory deserves attention.",
    evidence: velocity.map((x) => ({ label: x.name, value: `${x.avg_daily_units.toFixed(1)}/day`, detail: `${x.units_sold} units sold · ${money(x.revenue)} revenue · ${x.signal.replaceAll("_", " ")}` })),
  };
  const explain = () => onExplain?.(reasoning);
  return (
    <section className={`card ${onExplain ? "reasoningClickable" : ""}`} onClick={onExplain ? explain : undefined} onKeyDown={onExplain ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); explain(); } } : undefined} role={onExplain ? "button" : undefined} tabIndex={onExplain ? 0 : undefined}>
      <div className="cardTitle"><span><Icon name="box" className="icon" /></span><h3>Inventory signals</h3><small>Based on recent sales velocity</small></div>
      <div className="marginAlerts">{velocity.map((x) => <div className="marginRow" key={x.name}><span>{x.name}</span><b>{x.avg_daily_units.toFixed(1)}/day</b><em>{x.signal === "fast_mover" ? <span className="tag good">FAST MOVER</span> : <span className="tag">NORMAL</span>} · {money(x.revenue)}</em></div>)}</div>
    </section>
  );
}

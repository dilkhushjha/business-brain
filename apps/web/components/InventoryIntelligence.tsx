"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";
import type { ReasoningPayload } from "../lib/reasoning";

const money = (n: number) => { if (Math.abs(n) >= 100000) return "₹" + (n / 100000).toFixed(1) + "L"; if (Math.abs(n) >= 1000) return "₹" + (n / 1000).toFixed(1) + "K"; return "₹" + Math.round(n).toLocaleString("en-IN"); };
type VelocityRow = { name: string; units_sold: number; revenue: number; avg_daily_units: number; signal: string };
type StockRiskRow = { name: string; quantity_on_hand: number; avg_daily_units: number; days_of_cover: number; snapshot_date: string; severity: string };
type StockRisk = { stockout_risk: StockRiskRow[]; excess_inventory: StockRiskRow[] };
type InventoryPositionRow = { name: string; quantity_on_hand: number; ledger_inventory_value: number; source: string };

export default function InventoryIntelligence({ onExplain }: { onExplain?: (reasoning: ReasoningPayload) => void }) {
  const [velocity, setVelocity] = useState<VelocityRow[]>([]);
  const [stockRisk, setStockRisk] = useState<StockRisk | null>(null);
  const [position, setPosition] = useState<InventoryPositionRow[]>([]);
  useEffect(() => { Promise.all([apiFetch(`/inventory/${getBusinessId()}/signals?days=30&limit=8`).then(r => r.ok ? r.json() : []), apiFetch(`/inventory/${getBusinessId()}/stock-risk?limit=8`).then(r => r.ok ? r.json() : null), apiFetch(`/inventory/${getBusinessId()}/position?limit=20`).then(r => r.ok ? r.json() : [])]).then(([v,s,p]) => { setVelocity(v); setStockRisk(s); setPosition(p); }).catch(() => {}); }, []);
  const stockouts = stockRisk?.stockout_risk || [];
  const excess = stockRisk?.excess_inventory || [];
  const hasStockData = !!stockRisk && (stockouts.length > 0 || excess.length > 0);
  const fastMovers = velocity.filter(x => x.signal === "fast_mover");
  const topVelocity = [...velocity].sort((a,b) => b.avg_daily_units - a.avg_daily_units).slice(0,5);
  const riskCount = stockouts.length + excess.length;
  if (!velocity.length && !hasStockData && !position.length) return <div className="operationsEmpty"><Icon name="pulse" className="icon" /><div><b>No operational signals yet</b><p>Import sales or stock data to see inventory movement and operational risk.</p></div></div>;
  const reasoning: ReasoningPayload = { title: "Operations & inventory", value: hasStockData ? `${riskCount} inventory risks` : `${fastMovers.length} fast movers`, change: hasStockData ? `${excess.length} excess stock` : "Last 30 days", context: hasStockData ? "Based on stock-on-hand and recent sales velocity." : "Based on recent sales velocity; stock-on-hand data is not currently available.", why: "Days of cover compares stock on hand with average daily sales. Fast movers indicate demand pressure, but do not prove low stock.", implication: stockouts.length ? `Review replenishment for ${stockouts[0].name}.` : excess.length ? `Review purchasing for ${excess[0].name}.` : fastMovers.length ? "Review stock availability for fast-moving products." : "Continue monitoring operations.", evidence: topVelocity.map(x => ({ label: x.name, value: `${x.avg_daily_units.toFixed(1)}/day`, detail: `${x.units_sold} units · ${money(x.revenue)}` })) };
  return <div className="operationsDashboard">
    <div className="operationsSummary">
      <div className="operationsSummaryCard"><span className="eyebrow">OPERATIONAL STATUS</span><strong>{riskCount ? "Needs review" : "Monitoring"}</strong><p>{hasStockData ? `${riskCount} inventory risk signal${riskCount === 1 ? "" : "s"} detected.` : "Demand and inventory movement are being monitored."}</p></div>
      <div className="operationsStat"><span>Stockout risk</span><b>{stockouts.length}</b><small>{stockouts.length ? "items flagged" : "No items flagged"}</small></div>
      <div className="operationsStat"><span>Excess stock</span><b>{excess.length}</b><small>{excess.length ? "items flagged" : "No items flagged"}</small></div>
      <div className="operationsStat"><span>Fast movers</span><b>{fastMovers.length}</b><small>last 30 days</small></div>
    </div>
    <div className="operationsGrid">
      <section className="operationsCard"><div className="operationsCardHead"><div><span className="eyebrow">INVENTORY POSITION</span><h3>Stock on hand</h3></div><span className="operationsPeriod">Movement ledger</span></div>
        {position.length ? <div className="velocityList">{position.map(x => { const v = velocity.find(item => item.name === x.name); return <div className="velocityRow" key={x.name}><div><b>{x.name}</b><span>{x.quantity_on_hand} units · {money(x.ledger_inventory_value)}</span></div><strong>{v ? v.avg_daily_units.toFixed(1) : "0.0"}<small>/day</small></strong><span className={"operationsTag " + (v?.signal === "fast_mover" ? "fast" : "normal")}>{v?.signal === "fast_mover" ? "FAST MOVER" : "ON HAND"}</span></div>; })}</div> : <div className="operationsMuted">No inventory movements recorded yet.</div>}
        {hasStockData && <div className="stockRows">{[...stockouts.map(x => ({...x, kind:"stockout"})), ...excess.map(x => ({...x, kind:"excess"}))].map(x => <div className="stockRow" key={x.kind + x.name}><div className="stockRowTop"><div><b>{x.name}</b><span>{x.quantity_on_hand} on hand · {x.avg_daily_units.toFixed(1)}/day</span></div><strong>{x.days_of_cover.toFixed(0)}d</strong></div><div className="stockBar"><span style={{width: Math.min(100, Math.max(4, x.days_of_cover / 30 * 100)) + "%" }} /></div><div className="stockRowMeta"><span className={"operationsTag " + x.kind}>{x.kind === "stockout" ? "STOCKOUT RISK" : "EXCESS STOCK"}</span><span>{x.days_of_cover.toFixed(0)} days of cover</span></div></div>)}</div>}
      </section>>
      <aside className="operationsSide"><section className="operationsCard"><div className="operationsCardHead"><div><span className="eyebrow">DEMAND SIGNAL</span><h3>Fast movers</h3></div><span className="operationsCount">{fastMovers.length}</span></div>{fastMovers.length ? fastMovers.slice(0,5).map(x => <div className="fastMover" key={x.name}><div><b>{x.name}</b><span>{money(x.revenue)} revenue</span></div><strong>{x.avg_daily_units.toFixed(1)}<small>/day</small></strong></div>) : <div className="operationsMuted">No fast movers detected.</div>}</section>
      <section className="operationsCard operationsAction"><div className="operationsCardHead"><div><span className="eyebrow">NEXT REVIEW</span><h3>What to check</h3></div></div><div className="operationsGuidance"><Icon name={riskCount ? "alert" : "pulse"} className="icon" /><p>{stockouts.length ? `Review replenishment for ${stockouts[0].name} first.` : excess.length ? `Review purchasing for ${excess[0].name}.` : fastMovers.length ? "Check stock availability for your fastest-moving products." : "Continue monitoring operational movement."}</p></div></section></aside>
    </div>
    {onExplain && <button className="operationsExplain" onClick={() => onExplain(reasoning)}><Icon name="sparkle" className="icon" /> Explain these operational signals</button>}
  </div>;
}
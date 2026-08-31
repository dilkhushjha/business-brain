"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

type Product = { name: string; quantity: number; revenue: number };
type Customer = { name: string; orders: number; revenue: number };
type Concentration = { total_revenue: number; top_share_pct: number; risk: string; top_customers: Array<{ name: string; revenue: number; share_pct: number }> };
type Risk = { name: string; last_order: string | null; inactive_days: number | null; lifetime_revenue: number };
type Decline = { name: string; current_revenue: number; previous_revenue: number; change_pct: number; severity: string };

const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const pct = (n: number) => `${n >= 0 ? "+" : ""}${n.toFixed(0)}%`;

export default function PerformanceTables() {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [concentration, setConcentration] = useState<Concentration | null>(null);
  const [inactive, setInactive] = useState<Risk[]>([]);
  const [declining, setDeclining] = useState<Decline[]>([]);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/performance/${BUSINESS_ID}/products?days=30&limit=5`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/performance/${BUSINESS_ID}/customers?days=30&limit=5`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/customer-risk/${BUSINESS_ID}/concentration?top_n=5`).then(r => r.ok ? r.json() : null),
      fetch(`${API}/customer-risk/${BUSINESS_ID}/inactive?inactive_days=45&limit=5`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/customer-risk/${BUSINESS_ID}/declining?days=30&threshold=25&limit=5`).then(r => r.ok ? r.json() : []),
    ]).then(([p, c, concentrationData, inactiveData, decliningData]) => {
      setProducts(p);
      setCustomers(c);
      setConcentration(concentrationData);
      setInactive(inactiveData);
      setDeclining(decliningData);
    }).catch(() => {});
  }, []);

  if (!products.length && !customers.length && !concentration && !inactive.length && !declining.length) return null;

  return <>
    <section className="grid performanceGrid">
      <div className="card">
        <div className="cardTitle"><h3>Top products</h3><small>Last 30 days</small></div>
        {products.map((p, i) => <div className="performanceRow" key={p.name}>
          <span className="rank">{i + 1}</span>
          <div><b>{p.name}</b><small>{p.quantity} units sold</small></div>
          <strong>{money(p.revenue)}</strong>
        </div>)}
      </div>
      <div className="card">
        <div className="cardTitle"><h3>Top customers</h3><small>Last 30 days</small></div>
        {customers.map((c, i) => <div className="performanceRow" key={c.name}>
          <span className="rank">{i + 1}</span>
          <div><b>{c.name}</b><small>{c.orders} orders</small></div>
          <strong>{money(c.revenue)}</strong>
        </div>)}
      </div>
    </section>

    {(concentration || declining.length || inactive.length) && <>
      <div className="customerInsightIntro">
        <div><span className="eyebrow">CUSTOMER INTELLIGENCE</span><h3>Who needs attention?</h3></div>
        {concentration && <span className={`customerRiskBadge ${concentration.risk}`}>{concentration.risk.toUpperCase()} CONCENTRATION RISK</span>}
      </div>
      <section className="customerInsightGrid">
        {concentration && <div className="card customerInsightCard">
          <div className="cardTitle"><h3>Customer concentration</h3><small>Revenue dependency</small></div>
          <div className="customerHeadline"><strong>{concentration.top_share_pct.toFixed(0)}%</strong><span>of revenue comes from the top 5 customers</span></div>
          {concentration.top_customers.map((c, i) => <div className="customerMiniRow" key={c.name}>
            <span>{i + 1}</span><b>{c.name}</b><small>{c.share_pct.toFixed(0)}%</small><strong>{money(c.revenue)}</strong>
          </div>)}
        </div>}

        <div className="card customerInsightCard">
          <div className="cardTitle"><h3>Customers losing momentum</h3><small>Revenue decline</small></div>
          {declining.length ? declining.map(c => <div className="customerAlert" key={c.name}>
            <div><b>{c.name}</b><span className={`tag ${c.severity === "high" ? "danger" : "warning"}`}>{c.severity.toUpperCase()}</span></div>
            <p>Revenue changed <strong className="negative">{pct(c.change_pct)}</strong>, from {money(c.previous_revenue)} to {money(c.current_revenue)}.</p>
          </div>) : <p className="emptyInsight">No customers have crossed the decline threshold.</p>}
        </div>

        <div className="card customerInsightCard">
          <div className="cardTitle"><h3>Customers to follow up</h3><small>No recent orders</small></div>
          {inactive.length ? inactive.map(c => <div className="customerAlert" key={c.name}>
            <div><b>{c.name}</b><span className="tag warning">FOLLOW UP</span></div>
            <p>Last order {c.last_order || "unknown"} · <strong>{c.inactive_days ?? "—"} days inactive</strong> · lifetime {money(c.lifetime_revenue)}.</p>
          </div>) : <p className="emptyInsight">No inactive customers detected.</p>}
        </div>
      </section>
    </>}
  </>;
}

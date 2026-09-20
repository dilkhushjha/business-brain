"use client";

import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";



type Product = { name: string; quantity: number; revenue: number };
type Customer = { name: string; orders: number; revenue: number };
type Concentration = { total_revenue: number; top_share_pct: number; risk: string; top_customers: Array<{ name: string; revenue: number; share_pct: number }> };
type Risk = { name: string; last_order: string | null; inactive_days: number | null; lifetime_revenue: number };
type Decline = { name: string; current_revenue: number; previous_revenue: number; change_pct: number; severity: string };
type ProductConcentration = { total_revenue: number; top_share_pct: number; risk: string; top_products: Array<{ name: string; revenue: number; share_pct: number }> };
type ProductMomentum = { name: string; current_revenue: number; previous_revenue: number; change_pct: number; direction: string; severity: string };

const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const pct = (n: number) => `${n >= 0 ? "+" : ""}${n.toFixed(0)}%`;

export default function PerformanceTables({ section = "sales", dataVersion = 0 }: { section?: "sales" | "customers"; dataVersion?: number }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [concentration, setConcentration] = useState<Concentration | null>(null);
  const [inactive, setInactive] = useState<Risk[]>([]);
  const [declining, setDeclining] = useState<Decline[]>([]);
  const [productConcentration, setProductConcentration] = useState<ProductConcentration | null>(null);
  const [productMomentum, setProductMomentum] = useState<ProductMomentum[]>([]);

  useEffect(() => {
    setProducts([]);
    setCustomers([]);
    Promise.all([
      apiFetch(`/performance/${getBusinessId()}/products?days=30&limit=5&_v=${dataVersion}`).then((r) => (r.ok ? r.json() : [])),
      apiFetch(`/performance/${getBusinessId()}/customers?days=30&limit=5&_v=${dataVersion}`).then((r) => (r.ok ? r.json() : [])),
      apiFetch(`/customer-risk/${getBusinessId()}/concentration?top_n=5`).then((r) => (r.ok ? r.json() : null)),
      apiFetch(`/customer-risk/${getBusinessId()}/inactive?inactive_days=45&limit=5`).then((r) => (r.ok ? r.json() : [])),
      apiFetch(`/customer-risk/${getBusinessId()}/declining?days=30&threshold=25&limit=5`).then((r) => (r.ok ? r.json() : [])),
      apiFetch(`/product-risk/${getBusinessId()}/concentration?top_n=5`).then((r) => (r.ok ? r.json() : null)),
      apiFetch(`/product-risk/${getBusinessId()}/momentum?days=30&threshold=30&limit=5`).then((r) => (r.ok ? r.json() : [])),
    ]).then(([p, c, concentrationData, inactiveData, decliningData, productConcentrationData, productMomentumData]) => {
      setProducts(p);
      setCustomers(c);
      setConcentration(concentrationData);
      setInactive(inactiveData);
      setDeclining(decliningData);
      setProductConcentration(productConcentrationData);
      setProductMomentum(productMomentumData);
    }).catch(() => { });
  }, [dataVersion]);

  if (!products.length && !customers.length && !concentration && !inactive.length && !declining.length && !productConcentration && !productMomentum.length) return null;

  return (
    <>
      <section className="grid performanceGrid">
        {section === "sales" && <div className="card">
          <div className="cardTitle"><span><Icon name="trophy" className="icon" /></span><h3>Top products</h3><small>Last 30 days</small></div>
          {products.length ? products.map((p, i) => (
            <div className="performanceRow" key={p.name}>
              <span className="rank">{i + 1}</span>
              <div><b>{p.name}</b><small>{p.quantity} units sold</small></div>
              <strong>{money(p.revenue)}</strong>
            </div>
          )) : <p className="emptyInsight">No product sales found.</p>}
        </div>}
        {section === "customers" && <div className="card">
          <div className="cardTitle"><span><Icon name="users" className="icon" /></span><h3>Top customers</h3><small>Last 30 days</small></div>
          {customers.length ? customers.map((c, i) => (
            <div className="performanceRow" key={c.name}>
              <span className="rank">{i + 1}</span>
              <div><b>{c.name}</b><small>{c.orders} orders</small></div>
              <strong>{money(c.revenue)}</strong>
            </div>
          )) : <p className="emptyInsight">No customer sales found.</p>}
        </div>}
      </section>

      {section === "sales" && (productConcentration || productMomentum.length) && (
        <>
          <div className="customerInsightIntro">
            <div><span className="eyebrow">PRODUCT INTELLIGENCE</span><h3>What is driving the business?</h3></div>
            {productConcentration && <span className={`customerRiskBadge ${productConcentration.risk}`}>{productConcentration.risk.toUpperCase()} PRODUCT CONCENTRATION</span>}
          </div>
          <section className="customerInsightGrid">
            {productConcentration && (
              <div className="card customerInsightCard">
                <div className="cardTitle"><span><Icon name="layers" className="icon" /></span><h3>Revenue concentration</h3><small>All imported sales</small></div>
                <div className="customerHeadline"><strong>{productConcentration.top_share_pct.toFixed(0)}%</strong><span>of revenue comes from the top 5 products</span></div>
                {productConcentration.top_products.map((p, i) => (
                  <div className="customerMiniRow" key={p.name}>
                    <span>{i + 1}</span><b>{p.name}</b><small>{p.share_pct.toFixed(0)}%</small><strong>{money(p.revenue)}</strong>
                  </div>
                ))}
              </div>
            )}

            <div className="card customerInsightCard">
              <div className="cardTitle"><span><Icon name="trend" className="icon" /></span><h3>Products gaining or losing momentum</h3><small>30-day comparison</small></div>
              {productMomentum.length ? productMomentum.map((p) => (
                <div className="customerAlert" key={p.name}>
                  <div>
                    <b>{p.name}</b>
                    <span className={`tag ${p.direction === "up" ? "good" : p.severity === "high" ? "danger" : "warning"}`}>{p.direction === "up" ? "GROWING" : "DECLINING"}</span>
                  </div>
                  <p>Revenue moved from {money(p.previous_revenue)} to {money(p.current_revenue)} · <strong className={p.direction === "up" ? "positive" : "negative"}>{pct(p.change_pct)}</strong>.</p>
                </div>
              )) : <p className="emptyInsight">No product has crossed the current momentum threshold.</p>}
            </div>

            {productConcentration && (
              <div className="card customerInsightCard">
                <div className="cardTitle"><span><Icon name="bulb" className="icon" /></span><h3>Product action</h3><small>What the numbers suggest</small></div>
                <div className="customerAlert">
                  <div><b>{productConcentration.risk === "high" ? "Reduce dependency risk" : productConcentration.risk === "medium" ? "Watch product mix" : "Healthy product spread"}</b></div>
                  <p>{productConcentration.risk === "high" ? "A small number of products generate a large share of revenue. Protect availability, but avoid relying on them exclusively." : productConcentration.risk === "medium" ? "The leading products have meaningful revenue influence. Monitor their availability and margins closely." : "Revenue is reasonably distributed across products, reducing concentration risk."}</p>
                </div>
              </div>
            )}
          </section>
        </>
      )}

      {section === "customers" && (concentration || declining.length || inactive.length) && (
        <div className="customerCommandCenter">
          <div className="customerOverview">
            <div className="customerOverviewMain"><span className="eyebrow">CUSTOMER COMMAND CENTER</span><h3>Know who is driving revenue — and who needs attention.</h3><p>Recent customer activity, revenue dependency and retention signals in one view.</p></div>
            <div className={"customerHealth " + (declining.length || inactive.length ? "attention" : "healthy")}><b>{declining.length + inactive.length}</b><span>customers needing review</span></div>
          </div>
          <div className="customerMetrics">
            <div><span>Revenue concentration</span><b>{concentration ? concentration.top_share_pct.toFixed(0) + "%" : "—"}</b><small>top 5 customers</small></div>
            <div><span>Declining</span><b>{declining.length}</b><small>crossed decline threshold</small></div>
            <div><span>Follow up</span><b>{inactive.length}</b><small>no recent orders</small></div>
          </div>
          <div className="customerCommandGrid">
            {concentration && <section className="customerCommandCard customerLeaders"><div className="customerCommandHead"><div><span className="eyebrow">REVENUE LEADERS</span><h4>Top customers</h4></div><span>Last 30 days</span></div>{concentration.top_customers.map((c,i) => <div className="customerLeaderRow" key={c.name}><span>{i+1}</span><div><b>{c.name}</b><small>{c.share_pct.toFixed(0)}% of revenue</small></div><strong>{money(c.revenue)}</strong></div>)}</section>}
            <section className="customerCommandCard"><div className="customerCommandHead"><div><span className="eyebrow">RETENTION SIGNAL</span><h4>Customers losing momentum</h4></div><span>{declining.length}</span></div>{declining.length ? declining.map(c => <div className="customerSignalRow" key={c.name}><div><b>{c.name}</b><small>{money(c.previous_revenue)} → {money(c.current_revenue)}</small></div><strong className="negative">{pct(c.change_pct)}</strong></div>) : <div className="customerCommandEmpty">No customers have crossed the current decline threshold.</div>}</section>
            <section className="customerCommandCard"><div className="customerCommandHead"><div><span className="eyebrow">RETENTION SIGNAL</span><h4>Follow-up queue</h4></div><span>{inactive.length}</span></div>{inactive.length ? inactive.map(c => <div className="customerSignalRow" key={c.name}><div><b>{c.name}</b><small>Last order {c.last_order || "unknown"} · {c.inactive_days ?? "—"} days inactive</small></div><strong>{money(c.lifetime_revenue)}</strong></div>) : <div className="customerCommandEmpty">No inactive customers detected.</div>}</section>
            {concentration && <section className="customerCommandCard customerActionCard"><div className="customerCommandHead"><div><span className="eyebrow">RECOMMENDED REVIEW</span><h4>Customer dependency</h4></div></div><div className="customerAction"><Icon name="users" className="icon" /><p>{concentration.risk === "high" ? "A small group of customers contributes a large share of revenue. Protect these relationships while reducing dependency over time." : concentration.risk === "medium" ? "Leading customers have meaningful revenue influence. Monitor retention and avoid over-reliance on a small group." : "Revenue is reasonably distributed across customers. Continue monitoring concentration as the mix changes."}</p></div></section>}
          </div>
        </div>
      )}

    </>
  );
}
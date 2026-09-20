"use client";

import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";

const money = (n:number) => Math.abs(n)>=100000 ? "₹"+(n/100000).toFixed(1)+"L" : Math.abs(n)>=1000 ? "₹"+(n/1000).toFixed(1)+"K" : "₹"+Math.round(n).toLocaleString("en-IN");
type Supplier={name:string;purchases:number;amount:number;outstanding:number};
type Product={name:string;quantity:number;amount:number;unit_cost:number};
type SupplierInsight={name:string;invoice_count:number;spend:number;outstanding:number;share_pct:number;previous_spend:number;change_pct:number|null};
type CostChange={supplier:string;product:string;previous_unit_cost:number;current_unit_cost:number;change_pct:number};

export default function PurchaseIntelligence(){
 const [summary,setSummary]=useState<any>(null),[suppliers,setSuppliers]=useState<Supplier[]>([]),[products,setProducts]=useState<Product[]>([]),[insights,setInsights]=useState<SupplierInsight[]>([]),[costChanges,setCostChanges]=useState<CostChange[]>([]),[loading,setLoading]=useState(true);
 useEffect(()=>{const id=getBusinessId();Promise.all([
  apiFetch(`/purchases/${id}/summary?days=30`).then(r=>r.ok?r.json():null),
  apiFetch(`/purchases/${id}/suppliers?days=30&limit=5`).then(r=>r.ok?r.json():[]),
  apiFetch(`/purchases/${id}/products?days=30&limit=5`).then(r=>r.ok?r.json():[]),
  apiFetch(`/purchases/${id}/supplier-intelligence?days=90&limit=10`).then(r=>r.ok?r.json():null),
  apiFetch(`/purchases/${id}/supplier-cost-changes?days=90&threshold_pct=5&limit=10`).then(r=>r.ok?r.json():[])
  ]).then(([s,sp,p,si,cc])=>{setSummary(s);setSuppliers(sp);setProducts(p);setInsights(si?.suppliers||[]);setCostChanges(cc)}).catch(()=>{}).finally(()=>setLoading(false))},[]);
 if(loading)return <div className="card purchaseEmpty">Loading purchase intelligence…</div>;
 if(!summary?.invoice_count)return <div className="operationsEmpty"><Icon name="receipt" className="icon"/><div><b>No purchase data yet</b><p>Import purchase-register data to see supplier spend, purchased products and outstanding amounts.</p></div></div>;
 return <div className="purchaseDashboard">
  <div className="purchaseSummary">
   <div className="purchaseSummaryMain"><span className="eyebrow">PURCHASE HEALTH</span><strong>{summary.outstanding>0?"Supplier obligations need review":"Purchases are up to date"}</strong><p>Purchase activity and supplier obligations from the last 30 days.</p></div>
   <div className="purchaseStat"><span>Purchase spend</span><b>{money(summary.total_amount)}</b><small>last 30 days</small></div>
   <div className="purchaseStat"><span>Invoices</span><b>{summary.invoice_count}</b><small>purchase documents</small></div>
   <div className="purchaseStat"><span>Outstanding</span><b>{money(summary.outstanding)}</b><small>supplier payable</small></div>
  </div>
  <div className="purchaseGrid">
   <section className="card purchaseCard"><div className="purchaseHead"><div><span className="eyebrow">TOP SUPPLIERS</span><h3>Where purchase spend goes</h3></div><span>Last 30 days</span></div>{suppliers.map((s,i)=><div className="purchaseRow" key={s.name}><span className="purchaseRank">{i+1}</span><div><b>{s.name}</b><small>{s.purchases} invoices · {money(s.outstanding)} outstanding</small></div><strong>{money(s.amount)}</strong></div>)}</section>
   <section className="card purchaseCard"><div className="purchaseHead"><div><span className="eyebrow">TOP PURCHASED PRODUCTS</span><h3>What you're buying</h3></div><span>Last 30 days</span></div>{products.map((p,i)=><div className="purchaseRow" key={p.name}><span className="purchaseRank">{i+1}</span><div><b>{p.name}</b><small>{p.quantity.toLocaleString("en-IN")} units · avg {money(p.unit_cost)}/unit</small></div><strong>{money(p.amount)}</strong></div>)}</section>
  </div>
  {insights.length > 0 && <div className="purchaseGrid">
   <section className="card purchaseCard"><div className="purchaseHead"><div><span className="eyebrow">SUPPLIER DEPENDENCY</span><h3>Where spend is concentrated</h3></div><span>Last 90 days</span></div>{insights.slice(0,5).map((s,i)=><div className="purchaseRow" key={s.name}><span className="purchaseRank">{i+1}</span><div><b>{s.name}</b><small>{s.invoice_count} invoices · {s.share_pct}% of spend{s.change_pct == null ? "" : ` · ${s.change_pct > 0 ? "+" : ""}${s.change_pct}% vs prior period`}</small></div><strong>{money(s.spend)}</strong></div>)}</section>
   {costChanges.length > 0 && <section className="card purchaseCard"><div className="purchaseHead"><div><span className="eyebrow">COST PRESSURE</span><h3>Supplier price increases</h3></div><span>Last 90 days</span></div>{costChanges.slice(0,5).map(x=><div className="purchaseRow" key={x.supplier+x.product}><div><b>{x.product}</b><small>{x.supplier} · {money(x.previous_unit_cost)} → {money(x.current_unit_cost)}</small></div><strong>+{x.change_pct}%</strong></div>)}</section>}
  </div>}
 </div>;
}

"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

type CustomerRisk = { name: string; last_order: string | null; inactive_days: number | null; lifetime_revenue: number };
const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function CustomerRisk() {
  const [customers, setCustomers] = useState<CustomerRisk[]>([]);
  useEffect(() => {
    fetch(`${API}/customer-risk/${BUSINESS_ID}/inactive?inactive_days=45&limit=5`)
      .then(r => r.ok ? r.json() : [])
      .then(setCustomers).catch(() => {});
  }, []);
  if (!customers.length) return null;
  return <section className="card anomalyCard"><div className="cardTitle"><span>◌</span><h3>Customers at risk</h3></div>
    <p className="muted">Previously active customers with no order for 45+ days.</p>
    {customers.map(c => <div className="anomaly" key={c.name}><b>{c.name}</b><p>Last order: {c.last_order || "Unknown"} · <strong>{c.inactive_days} days inactive</strong> · Lifetime revenue {money(c.lifetime_revenue)}</p><span className="tag warning">FOLLOW UP</span></div>)}
  </section>;
}

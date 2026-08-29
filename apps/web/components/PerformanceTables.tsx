"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

type Product = { name: string; quantity: number; revenue: number };
type Customer = { name: string; orders: number; revenue: number };
const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function PerformanceTables() {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/performance/${BUSINESS_ID}/products?days=30&limit=5`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/performance/${BUSINESS_ID}/customers?days=30&limit=5`).then(r => r.ok ? r.json() : []),
    ]).then(([p, c]) => { setProducts(p); setCustomers(c); }).catch(() => {});
  }, []);

  if (!products.length && !customers.length) return null;
  return <section className="grid performanceGrid">
    <div className="card"><div className="cardTitle"><span>▦</span><h3>Top products</h3></div>
      {products.map((p, i) => <div className="performanceRow" key={p.name}><span className="rank">{i + 1}</span><div><b>{p.name}</b><small>{p.quantity} units</small></div><strong>{money(p.revenue)}</strong></div>)}
    </div>
    <div className="card"><div className="cardTitle"><span>♙</span><h3>Top customers</h3></div>
      {customers.map((c, i) => <div className="performanceRow" key={c.name}><span className="rank">{i + 1}</span><div><b>{c.name}</b><small>{c.orders} orders</small></div><strong>{money(c.revenue)}</strong></div>)}
    </div>
  </section>;
}

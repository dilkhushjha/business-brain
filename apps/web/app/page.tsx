"use client";

import { FormEvent, useState } from "react";

const demo = { revenue: "₹8.50L", change: "-15.0%", customers: "127", avgOrder: "₹6,700" };

export default function Home() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  function ask(event: FormEvent) { event.preventDefault(); if (!question.trim()) return; setAnswer("Business Brain is ready to connect this question to your evidence-backed analytics API."); }
  return <main className="shell">
    <header className="header"><div><span className="eyebrow">BUSINESS BRAIN</span><h1>Your business, understood.</h1></div><span className="status">● Demo data</span></header>
    <section className="hero"><p className="muted">Electrical wholesaler · August 2026</p><h2>Good morning 👋</h2><p className="muted">Here are the signals that deserve your attention.</p></section>
    <section className="metrics"><Metric label="Revenue" value={demo.revenue} change={demo.change}/><Metric label="Customers" value={demo.customers} change="-4.0%"/><Metric label="Avg. order" value={demo.avgOrder} change="+6.1%"/></section>
    <section className="grid">
      <div className="card"><div className="cardTitle"><span>⚠</span><h3>Things needing attention</h3></div><div className="signal"><b>Revenue declined 15%</b><p>The decline should be investigated before assuming it is market-wide.</p><span className="tag danger">HIGH</span></div><div className="signal"><b>Customer concentration</b><p>A small number of customers account for a significant share of sales.</p><span className="tag warning">REVIEW</span></div></div>
      <div className="card"><div className="cardTitle"><span>✦</span><h3>Positive signals</h3></div><div className="signal"><b>Average order value is up 6.1%</b><p>Higher order values are partially offsetting the sales decline.</p><span className="tag good">POSITIVE</span></div><div className="signal"><b>LED 9W is accelerating</b><p>Product-level momentum is worth checking against inventory.</p><span className="tag good">POSITIVE</span></div></div>
    </section>
    <section className="ask card"><span className="eyebrow">ASK BUSINESS BRAIN</span><h3>What do you want to know?</h3><form onSubmit={ask}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Why did my sales fall?"/><button>Ask →</button></form>{answer && <p className="response">{answer}</p>}</section>
  </main>;
}
function Metric({label,value,change}:{label:string;value:string;change:string}) { return <div className="metric"><span>{label}</span><strong>{value}</strong><small>{change}</small></div>; }

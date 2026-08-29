"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Evidence = { metric?: string; value?: string; metadata?: { change?: number } };
type Context = { evidence?: Evidence[]; signals?: Array<Record<string, unknown>>; recommendations?: Array<Record<string, unknown>> };
type KPI = { name: string; value: string | null; unit?: string; comparison_value?: string | null; change?: string | null };

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

const DEMO_CONTEXT: Context = {
  evidence: [{ metric: "revenue", value: "850000", metadata: { change: -0.15 } }],
  signals: [
    { title: "Revenue declined 15%", message: "Revenue fell from ₹10.0L to ₹8.5L versus the previous period.", severity: "high" },
    { title: "Customer concentration", message: "Two customers account for a large share of the decline and should be reviewed.", severity: "medium" },
    { title: "LED 9W is accelerating", message: "Sales momentum is positive; check inventory before demand increases further.", severity: "positive" },
  ],
  recommendations: [
    { title: "Investigate the revenue decline", description: "Start with the customers and products contributing most to the ₹1.5L decline." },
    { title: "Review LED 9W inventory", description: "Positive product momentum may create a stock opportunity." },
  ],
};

function demoAnswer(question: string) {
  const q = question.toLowerCase();
  if (q.includes("why") && (q.includes("sales") || q.includes("revenue"))) return "Revenue fell 15%, from ₹10.0L to ₹8.5L. The demo evidence indicates the decline is concentrated in a small number of customers rather than being uniform across the business. The next investigation should compare those customers' recent orders and the products they stopped or reduced buying. This is demo data, so no customer-specific cause is asserted without supporting evidence.";
  if (q.includes("doing") || q.includes("health")) return "The business is showing a mixed picture: revenue is down 15%, while average order value and LED 9W momentum are positive. The highest-priority issue is understanding the ₹1.5L revenue decline.";
  return `For the demo business, I can currently answer questions using the available evidence. You asked: “${question}”. Try asking “Why did my sales fall?” or “How is my business doing?”`;
}

export default function Home() {
  const [context, setContext] = useState<Context | null>(null);
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${API}/context/${BUSINESS_ID}`).then(r => { if (!r.ok) throw new Error(`Context API returned ${r.status}`); return r.json(); }),
      fetch(`${API}/kpis/sales/${BUSINESS_ID}`).then(r => { if (!r.ok) throw new Error(`KPI API returned ${r.status}`); return r.json(); }),
    ])
      .then(([data, salesKpis]) => { setContext(data); setKpis(salesKpis); setLive(true); })
      .catch(() => { setContext(DEMO_CONTEXT); setLive(false); })
      .finally(() => setLoading(false));
  }, []);

  const revenue = useMemo(() => context?.evidence?.find(e => e.metric === "revenue"), [context]);
  const signalCount = context?.signals?.length ?? 0;
  const recommendationCount = context?.recommendations?.length ?? 0;
  const findKpi = (...names: string[]) => kpis.find(k => names.some(n => k.name.toLowerCase().includes(n)));
  const revenueKpi = findKpi("revenue");
  const ordersKpi = findKpi("order", "sales");
  const aovKpi = findKpi("average", "aov");
  const customersKpi = findKpi("customer");

  async function ask(event: FormEvent) {
    event.preventDefault(); if (!question.trim()) return;
    setAsking(true); setAnswer(""); setError("");
    if (!live) { setTimeout(() => { setAnswer(demoAnswer(question)); setAsking(false); }, 450); return; }
    try {
      const response = await fetch(`${API}/agent/${BUSINESS_ID}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
      if (!response.ok) throw new Error(`Agent returned ${response.status}`);
      const data = await response.json(); setAnswer(data.answer);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to reach Business Brain"); }
    finally { setAsking(false); }
  }

  const revenueDisplay = revenueKpi?.value != null ? `₹${Number(revenueKpi.value).toLocaleString("en-IN")}` : revenue?.value ? `₹${Number(revenue.value).toLocaleString("en-IN")}` : "—";
  return <main className="shell">
    <header className="header"><div><span className="eyebrow">BUSINESS BRAIN</span><h1>Your business, understood.</h1></div><div><a className="status" href="/import">＋ Import data</a> <span className={`status ${loading ? "loading" : live ? "" : "demo"}`}>● {loading ? "Connecting…" : live ? "Live data" : "Demo mode"}</span></div></header>
    {!live && !loading && <div className="demoBanner"><strong>DEMO MODE</strong><span>Showing a safe synthetic electrical-wholesaler scenario. No real business data is being displayed.</span></div>}
    <section className="hero"><p className="muted">Electrical wholesaler · Evidence-backed intelligence</p><h2>Good morning 👋</h2><p className="muted">Here are the signals Business Brain found in the business data.</p></section>
    <section className="metrics">
      <Metric label="Revenue" value={revenueDisplay} change={revenueKpi?.change ? `${revenueKpi.change}%` : revenue?.metadata?.change != null ? `${(revenue.metadata.change * 100).toFixed(1)}%` : "—"}/>
      <Metric label="Orders" value={ordersKpi?.value ?? "—"} change={ordersKpi?.change ? `${ordersKpi.change}%` : "30-day period"}/>
      <Metric label="Avg. Order Value" value={aovKpi?.value ? `₹${Number(aovKpi.value).toLocaleString("en-IN")}` : "—"} change="30-day period"/>
      <Metric label="Active Customers" value={customersKpi?.value ?? "—"} change="30-day period"/>
    </section>
    {error && <div className="errorBox">{error}</div>}
    <section className="grid"><div className="card"><div className="cardTitle"><span>⚠</span><h3>Things needing attention</h3></div>{context?.signals?.map((s,i)=><div className="signal" key={i}><b>{String(s.title || s.name || "Business signal")}</b><p>{String(s.message || s.description || "Review this signal.")}</p><span className={`tag ${s.severity === "high" ? "danger" : "warning"}`}>{String(s.severity || "REVIEW").toUpperCase()}</span></div>)}</div><div className="card"><div className="cardTitle"><span>✦</span><h3>Recommendations</h3></div>{context?.recommendations?.map((r,i)=><div className="signal" key={i}><b>{String(r.title || r.name || "Recommendation")}</b><p>{String(r.description || r.message || "Evidence-backed action available.")}</p><span className="tag good">ACTION</span></div>)}</div></section>
    <section className="ask card"><span className="eyebrow">ASK BUSINESS BRAIN</span><h3>What do you want to know?</h3><form onSubmit={ask}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Why did my sales fall?" disabled={asking}/><button disabled={asking}>{asking ? "Thinking…" : "Ask →"}</button></form>{answer && <div className="response"><strong>Business Brain {live ? "· Live" : "· Demo"}</strong><p>{answer}</p></div>}</section>
  </main>;
}
function Metric({label,value,change}:{label:string;value:string;change:string}) { return <div className="metric"><span>{label}</span><strong>{value}</strong><small>{change}</small></div>; }

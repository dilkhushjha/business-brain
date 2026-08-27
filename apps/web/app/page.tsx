"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Evidence = { metric?: string; value?: string; metadata?: { change?: number } };
type Context = { evidence?: Evidence[]; signals?: Array<Record<string, unknown>>; recommendations?: Array<Record<string, unknown>> };

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

export default function Home() {
  const [context, setContext] = useState<Context | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/context/${BUSINESS_ID}`)
      .then(r => { if (!r.ok) throw new Error(`API returned ${r.status}`); return r.json(); })
      .then(setContext).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, []);

  const revenue = useMemo(() => context?.evidence?.find(e => e.metric === "revenue"), [context]);
  const change = revenue?.metadata?.change;

  async function ask(event: FormEvent) {
    event.preventDefault(); if (!question.trim()) return;
    setAsking(true); setAnswer(""); setError("");
    try {
      const response = await fetch(`${API}/agent/${BUSINESS_ID}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
      if (!response.ok) throw new Error(`Agent returned ${response.status}`);
      const data = await response.json(); setAnswer(data.answer);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to reach Business Brain"); }
    finally { setAsking(false); }
  }

  const signalCount = context?.signals?.length ?? 0;
  const recommendationCount = context?.recommendations?.length ?? 0;

  return <main className="shell">
    <header className="header"><div><span className="eyebrow">BUSINESS BRAIN</span><h1>Your business, understood.</h1></div><span className={`status ${loading ? "loading" : error ? "error" : ""}`}>● {loading ? "Connecting…" : error ? "Offline" : "Live data"}</span></header>
    <section className="hero"><p className="muted">Business intelligence · Evidence-backed</p><h2>Good morning 👋</h2><p className="muted">Here are the signals Business Brain found in your data.</p></section>
    <section className="metrics"><Metric label="Revenue" value={revenue?.value ? `₹${Number(revenue.value).toLocaleString("en-IN")}` : "—"} change={change != null ? `${change > 0 ? "+" : ""}${(change * 100).toFixed(1)}%` : "—"}/><Metric label="Signals" value={String(signalCount)} change="needs attention"/><Metric label="Recommendations" value={String(recommendationCount)} change="evidence-backed"/></section>
    {error && <div className="errorBox">Could not load live Business Brain data: {error}</div>}
    <section className="grid">
      <div className="card"><div className="cardTitle"><span>⚠</span><h3>Things needing attention</h3></div>{signalCount ? context?.signals?.map((s, i) => <div className="signal" key={i}><b>{String(s.title || s.name || "Business signal")}</b><p>{String(s.message || s.description || "Review this signal in the intelligence layer.")}</p><span className="tag warning">REVIEW</span></div>) : <p className="muted">No active signals returned.</p>}</div>
      <div className="card"><div className="cardTitle"><span>✦</span><h3>Recommendations</h3></div>{recommendationCount ? context?.recommendations?.map((r, i) => <div className="signal" key={i}><b>{String(r.title || r.name || "Recommendation")}</b><p>{String(r.description || r.message || "Evidence-backed action available.")}</p><span className="tag good">ACTION</span></div>) : <p className="muted">No recommendations returned.</p>}</div>
    </section>
    <section className="ask card"><span className="eyebrow">ASK BUSINESS BRAIN</span><h3>What do you want to know?</h3><form onSubmit={ask}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Why did my sales fall?" disabled={asking}/><button disabled={asking}>{asking ? "Thinking…" : "Ask →"}</button></form>{answer && <div className="response"><strong>Business Brain</strong><p>{answer}</p></div>}</section>
  </main>;
}
function Metric({label,value,change}:{label:string;value:string;change:string}) { return <div className="metric"><span>{label}</span><strong>{value}</strong><small>{change}</small></div>; }

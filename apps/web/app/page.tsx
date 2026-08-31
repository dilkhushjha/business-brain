"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import RevenueTrend from "../components/RevenueTrend";
import PerformanceTables from "../components/PerformanceTables";
import MarginIntelligence from "../components/MarginIntelligence";
import ReceivablesIntelligence from "../components/ReceivablesIntelligence";
import InventoryIntelligence from "../components/InventoryIntelligence";
import DataFreshness from "../components/DataFreshness";

type Evidence = { metric?: string; value?: string; metadata?: { change?: number } };
type Context = {
  evidence?: Evidence[];
  signals?: Array<Record<string, unknown>>;
  recommendations?: Array<Record<string, unknown>>;
};
type KPI = { name: string; value: string | null; change?: string | null; period?: string };
type Anomaly = { name: string; change_pct: number; severity: string };

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "11111111-1111-1111-1111-111111111111";

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

const SUGGESTED_QUESTIONS = ["Why did my sales fall?", "How is the business doing overall?", "Which customers need follow-up?"];

function demoAnswer(q: string) {
  const s = q.toLowerCase();
  if (s.includes("why") && (s.includes("sales") || s.includes("revenue")))
    return "Revenue fell 15%, from ₹10.0L to ₹8.5L. The evidence indicates the decline is concentrated in a small number of customers. Compare those customers' recent orders and the products they reduced.";
  if (s.includes("doing") || s.includes("health"))
    return "The business is mixed: revenue is down 15%, while average order value and LED 9W momentum are positive. The priority is understanding the revenue decline.";
  if (s.includes("follow") || s.includes("customer"))
    return "Start with customers who have gone quiet for 45+ days and have meaningful lifetime revenue — they're the fastest wins for re-engagement.";
  return `I can answer using the available business evidence. You asked: "${q}".`;
}

const pct = (v: string | number | null | undefined) => {
  if (v === null || v === undefined || v === "") return "—";
  const n = Number(v);
  return Number.isFinite(n) ? `${n >= 0 ? "+" : ""}${n.toFixed(0)}%` : "—";
};
const money = (v: string | null | undefined) => {
  if (v == null || v === "") return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`;
  if (Math.abs(n) >= 100000) return `₹${(n / 100000).toFixed(2)}L`;
  if (Math.abs(n) >= 1000) return `₹${(n / 1000).toFixed(1)}K`;
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
};

type IconName = "wallet" | "invoice" | "trend" | "receipt" | "alert" | "check" | "pulse" | "chat" | "sparkle" | "arrow";
const ICON_PATHS: Record<IconName, string> = {
  wallet: "M3 7a2 2 0 012-2h13a1 1 0 011 1v3M3 7v10a2 2 0 002 2h15a1 1 0 001-1v-6a1 1 0 00-1-1h-4a2 2 0 100 4h5M3 7l3-4h9",
  invoice: "M7 3h10a1 1 0 011 1v16l-3-2-3 2-3-2-3 2V4a1 1 0 011-1zM9 8h6M9 12h6M9 16h3",
  trend: "M3 17l6-6 4 4 8-8M21 7h-6v6",
  receipt: "M6 2h12v20l-3-2-3 2-3-2-3 2V2zM9 7h6M9 11h6M9 15h4",
  alert: "M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
  check: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  pulse: "M3 12h4l3 8 4-16 3 8h4",
  chat: "M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z",
  sparkle: "M12 3l1.8 4.9L19 9.7l-4.9 1.8L12 16.4l-1.8-4.9L5 9.7l4.9-1.8L12 3zM19 15l.9 2.4 2.4.9-2.4.9-.9 2.4-.9-2.4-2.4-.9 2.4-.9.9-2.4z",
  arrow: "M5 12h14M13 6l6 6-6 6",
};
function Icon({ name, className }: { name: IconName; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d={ICON_PATHS[name]} />
    </svg>
  );
}

function Metric({ label, value, change, note, icon, tone = "primary" }: { label: string; value: string; change: string; note: string; icon: IconName; tone?: "primary" | "success" | "danger" | "amber" }) {
  const up = change.startsWith("+") && change !== "+0%";
  const down = change.startsWith("-");
  return (
    <div className={`metric tone-${tone}`}>
      <div className="metricTop">
        <span className="metricLabel">{label}</span>
        <span className="iconChip"><Icon name={icon} className="icon" /></span>
      </div>
      <strong>{value}</strong>
      <div className="metricMeta">
        {change ? <small className={up ? "positive delta" : down ? "negative delta" : "delta"}>{up ? "▲" : down ? "▼" : ""} {change}</small> : null}
        <small className="metricNote">{note}</small>
      </div>
    </div>
  );
}

function severityIcon(severity?: string): { icon: IconName; tone: string } {
  if (severity === "high") return { icon: "alert", tone: "danger" };
  if (severity === "positive") return { icon: "check", tone: "success" };
  return { icon: "pulse", tone: "amber" };
}

export default function Home() {
  const [context, setContext] = useState<Context | null>(null);
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      fetch(`${API}/context/${BUSINESS_ID}`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
      fetch(`${API}/kpis/sales/${BUSINESS_ID}`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
      fetch(`${API}/anomalies/${BUSINESS_ID}?days=30&limit=5`).then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([a, b, c]) => { setContext(a); setKpis(b); setAnomalies(c); setLive(true); })
      .catch(() => { setContext(DEMO_CONTEXT); setLive(false); })
      .finally(() => setLoading(false));
  }, []);

  const greeting = useMemo(() => {
    const h = new Date().getHours();
    return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  }, []);
  const today = useMemo(() => new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" }), []);

  const revenue = useMemo(() => context?.evidence?.find((e) => e.metric === "revenue"), [context]);
  const find = (...n: string[]) => kpis.find((k) => n.some((x) => k.name.toLowerCase().includes(x)) && k.period !== "all_time");
  const totalRevenue = kpis.find((k) => k.name === "total_revenue");
  const totalInvoices = kpis.find((k) => k.name === "total_invoice_count");
  const rk = find("revenue"), ak = find("average", "aov");
  const revenueChange = rk?.change ?? (revenue?.metadata?.change != null ? revenue.metadata.change * 100 : null);
  const highSignals = (context?.signals || []).filter((s) => s.severity === "high");
  const positiveSignals = (context?.signals || []).filter((s) => s.severity === "positive");
  const health = highSignals.length >= 2 ? "Needs attention" : highSignals.length === 1 ? "Watch closely" : "On track";
  const healthText =
    health === "Needs attention" ? "A few issues deserve attention today. Start with the highest-impact signals below."
      : health === "Watch closely" ? "Performance is mixed. Review the highlighted signal before making decisions."
        : "No major warning signals are currently visible.";
  const healthIcon = health === "Needs attention" ? "alert" : health === "Watch closely" ? "pulse" : "check";
  const healthTone = health === "Needs attention" ? "danger" : health === "Watch closely" ? "amber" : "success";

  async function runQuestion(q: string) {
    if (!q.trim()) return;
    setAsking(true); setAnswer(""); setError("");
    if (!live) { setTimeout(() => { setAnswer(demoAnswer(q)); setAsking(false); }, 300); return; }
    try {
      const r = await fetch(`${API}/agent/${BUSINESS_ID}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
      if (!r.ok) throw Error(`Agent returned ${r.status}`);
      setAnswer((await r.json()).answer);
    } catch (x) {
      setError(x instanceof Error ? x.message : "Unable to reach Business Brain");
    } finally {
      setAsking(false);
    }
  }
  function ask(e: FormEvent) { e.preventDefault(); runQuestion(question); }
  function askSuggested(q: string) { setQuestion(q); runQuestion(q); }

  return (
    <main className="shell">
      <header className="header">
        <div className="brand">
          <span className="brandMark"><Icon name="sparkle" className="icon" /></span>
          <div>
            <span className="eyebrow">BUSINESS BRAIN</span>
            <h1>Your business, understood.</h1>
          </div>
        </div>
        <div className="headerRight">
          <a className="status" href="/import">Import data</a>
          <span className={`status ${loading ? "loading" : live ? "live" : "demo"}`}>
            <span className="statusDot" /> {loading ? "Connecting…" : live ? "Live data" : "Demo mode"}
          </span>
        </div>
      </header>

      {!live && !loading && (
        <div className="demoBanner"><strong>DEMO MODE</strong><span>Sample electrical-wholesaler scenario · safe for testing</span></div>
      )}

      <section className="hero">
        <div className="heroGlow" aria-hidden="true" />
        <p className="muted">{today} · Evidence-backed intelligence</p>
        <h2>{greeting}.</h2>
        <p className="muted">Here is what changed, what needs attention, and where to act.</p>
        <DataFreshness />
      </section>

      <section className="healthBar">
        <div className={`healthPanel tone-${healthTone}`}>
          <span className="iconChip lg"><Icon name={healthIcon} className="icon" /></span>
          <div>
            <span className="eyebrow">BUSINESS HEALTH</span>
            <h3>{health}</h3>
            <p>{healthText}</p>
          </div>
        </div>
        <div className="healthFacts">
          <div>
            <span className="iconChip sm tone-danger"><Icon name="alert" className="icon" /></span>
            <b>{highSignals.length}</b><span>priority concerns</span>
          </div>
          <div>
            <span className="iconChip sm tone-success"><Icon name="check" className="icon" /></span>
            <b>{positiveSignals.length}</b><span>positive signals</span>
          </div>
        </div>
      </section>

      <section className="sectionHeading"><span>BUSINESS OVERVIEW</span><small>All imported data + current period</small></section>
      <section className="metrics">
        <Metric label="Total Revenue" value={money(totalRevenue?.value ?? revenue?.value)} change="" note="all imported data" icon="wallet" tone="primary" />
        <Metric label="Total Invoices" value={totalInvoices?.value ?? "—"} change="" note="all imported data" icon="invoice" tone="primary" />
        <Metric label="Current Month Revenue" value={money(rk?.value)} change={pct(revenueChange)} note="vs previous month" icon="trend" tone={revenueChange == null ? "primary" : Number(revenueChange) < 0 ? "danger" : "success"} />
        <Metric label="Average Invoice Value" value={money(ak?.value)} change={pct(ak?.change)} note="current month" icon="receipt" tone="amber" />
      </section>

      <div className="dashboardGrid">
        <div>
          <section className="sectionHeading"><span>SALES PERFORMANCE</span><small>Revenue and commercial momentum</small></section>
          <RevenueTrend />
          <PerformanceTables />
          <section className="sectionHeading"><span>PROFITABILITY &amp; CASH</span><small>Where revenue becomes profit and cash</small></section>
          <div className="statGrid">
            <MarginIntelligence />
            <ReceivablesIntelligence />
          </div>
          <InventoryIntelligence />
        </div>

        <aside>
          <section className="sectionHeading"><span>MANAGEMENT ATTENTION</span><small>Highest-priority signals</small></section>
          <section className="card signalCard">
            {context?.signals?.slice(0, 4).map((s, i) => {
              const sev = severityIcon(s.severity as string | undefined);
              return (
                <div className="signal" key={i}>
                  <span className={`iconChip sm tone-${sev.tone}`}><Icon name={sev.icon} className="icon" /></span>
                  <div className="signalBody">
                    <div className="signalTop">
                      <b>{String(s.title || s.name || "Business signal")}</b>
                      <span className={`tag ${s.severity === "high" ? "danger" : s.severity === "positive" ? "good" : "warning"}`}>{String(s.severity || "REVIEW").toUpperCase()}</span>
                    </div>
                    <p>{String(s.message || s.description || "Review this signal.")}</p>
                  </div>
                </div>
              );
            })}
          </section>

          <section className="sectionHeading"><span>RECOMMENDED ACTIONS</span><small>What to do next</small></section>
          <section className="card actionCard">
            {context?.recommendations?.map((r, i) => (
              <div className="signal" key={i}>
                <div className="actionNo">{i + 1}</div>
                <div className="signalBody">
                  <b>{String(r.title || r.name || "Recommendation")}</b>
                  <p>{String(r.description || r.message || "Evidence-backed action available.")}</p>
                </div>
              </div>
            ))}
          </section>
        </aside>
      </div>

      {anomalies.length > 0 && (
        <>
          <section className="sectionHeading"><span>EXCEPTIONS</span><small>Unusual movements worth investigating</small></section>
          <section className="card anomalyCard">
            {anomalies.map((a, i) => (
              <div className="anomaly" key={i}>
                <span className={`iconChip sm tone-${a.severity === "high" ? "danger" : "amber"}`}><Icon name="alert" className="icon" /></span>
                <div className="signalBody">
                  <div className="signalTop">
                    <b>{a.name}</b>
                    <span className={`tag ${a.severity === "high" ? "danger" : "warning"}`}>{a.severity.toUpperCase()}</span>
                  </div>
                  <p>Revenue {a.change_pct >= 0 ? "increased" : "decreased"} <strong>{Math.abs(a.change_pct).toFixed(0)}%</strong> versus the prior period.</p>
                </div>
              </div>
            ))}
          </section>
        </>
      )}

      {error && <div className="errorBox">{error}</div>}

      <section className="ask card">
        <div className="askHead">
          <span className="iconChip"><Icon name="chat" className="icon" /></span>
          <div><span className="eyebrow">ASK BUSINESS BRAIN</span><h3>Ask about your business</h3></div>
        </div>
        <div className="suggestions">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button type="button" className="suggestionChip" key={q} onClick={() => askSuggested(q)} disabled={asking}>{q}</button>
          ))}
        </div>
        <form onSubmit={ask}>
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Why did my sales fall?" disabled={asking} />
          <button disabled={asking}>{asking ? "Thinking…" : "Ask"}</button>
        </form>
        {answer && (
          <div className="response">
            <strong>Business Brain {live ? "· Live" : "· Demo"}</strong>
            <p>{answer}</p>
          </div>
        )}
      </section>
    </main>
  );
}
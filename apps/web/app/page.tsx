"use client";

import { ChangeEvent, DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import RevenueTrend from "../components/RevenueTrend";
import PerformanceTables from "../components/PerformanceTables";
import MarginIntelligence from "../components/MarginIntelligence";
import ReceivablesIntelligence from "../components/ReceivablesIntelligence";
import InventoryIntelligence from "../components/InventoryIntelligence";
import ConnectGate from "../components/ConnectGate";
import DashboardReasoningOverlay from "../components/DashboardReasoningOverlay";
import { ApiAuthError, apiFetch, clearSession, getBusinessId, getCurrentUser, hasToken, type SessionUser } from "../lib/api";
import { buildHealthReasoning, buildMetricReasoning, type ReasoningPayload } from "../lib/reasoning";

type Evidence = { metric?: string; value?: string; metadata?: { change?: number } };
type Context = {
  entities?: Array<{ entity_type?: string; label?: string }>;
  evidence?: Evidence[];
  signals?: Array<Record<string, unknown>>;
  recommendations?: Array<Record<string, unknown>>;
};
type KPI = { name: string; value: string | null; change?: string | null; period?: string };
type Anomaly = { name: string; change_pct: number; severity: string };

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

type IconName = "wallet" | "invoice" | "trend" | "receipt" | "alert" | "check" | "pulse" | "chat" | "sparkle" | "arrow" | "user";
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
  user: "M20 21a8 8 0 00-16 0M12 13a4 4 0 100-8 4 4 0 000 8z",
};
function Icon({ name, className }: { name: IconName; className?: string }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}><path d={ICON_PATHS[name]} /></svg>;
}

function Metric({ label, value, change, note, icon, tone = "primary", onClick }: { label: string; value: string; change: string; note: string; icon: IconName; tone?: "primary" | "success" | "danger" | "amber"; onClick?: () => void }) {
  const up = change.startsWith("+") && change !== "+0%";
  const down = change.startsWith("-");
  const clickable = Boolean(onClick);
  return <div className={`metric tone-${tone}${clickable ? " metricClickable" : ""}`} onClick={onClick} onKeyDown={(event) => { if (clickable && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); onClick?.(); } }} role={clickable ? "button" : undefined} tabIndex={clickable ? 0 : undefined} aria-label={clickable ? `Explain ${label}` : undefined}>
    <div className="metricTop"><span className="metricLabel">{label}</span><span className="iconChip"><Icon name={icon} className="icon" /></span></div>
    <strong>{value}</strong>
    <div className="metricMeta">{change ? <small className={up ? "positive delta" : down ? "negative delta" : "delta"}>{up ? "▲" : down ? "▼" : ""} {change}</small> : null}<small className="metricNote">{note}</small></div>
  </div>;
}

type SignalSeverity = "critical" | "warning" | "high" | "positive" | "info" | "medium" | "unknown";

function normalizeSeverity(severity?: string): SignalSeverity {
  const value = String(severity || "").trim().toLowerCase();
  if (value === "critical" || value === "warning" || value === "high" || value === "positive" || value === "info" || value === "medium") return value;
  return "unknown";
}

function isPrioritySeverity(severity?: string) {
  return ["critical", "warning", "high"].includes(normalizeSeverity(severity));
}

function isPositiveSeverity(severity?: string) {
  return ["positive", "info"].includes(normalizeSeverity(severity));
}
function severityRank(severity?: string) {
  const normalized = normalizeSeverity(severity);
  if (normalized === "critical") return 0;
  if (normalized === "warning") return 1;
  if (normalized === "high") return 2;
  if (normalized === "medium") return 3;
  if (normalized === "info") return 4;
  if (normalized === "positive") return 5;
  return 6;
}


function severityIcon(severity?: string): { icon: IconName; tone: string } {
  const normalized = normalizeSeverity(severity);
  if (isPrioritySeverity(normalized)) return { icon: "alert", tone: "danger" };
  if (isPositiveSeverity(normalized)) return { icon: "check", tone: "success" };
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
  const [connected, setConnected] = useState(false);
  const [checkedAuth, setCheckedAuth] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const [user, setUser] = useState<SessionUser | null>(null);
  const [selectedReasoning, setSelectedReasoning] = useState<ReasoningPayload | null>(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [chatOpen, setChatOpen] = useState(false);
  const [dataVersion, setDataVersion] = useState(0);

  useEffect(() => {
    if (!hasToken()) { setConnected(false); setCheckedAuth(true); return; }
    getCurrentUser().then((current) => { setUser(current); setConnected(true); }).catch(() => { clearSession(); setConnected(false); }).finally(() => setCheckedAuth(true));
  }, []);

  useEffect(() => {
    function closeProfile(event: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) setProfileOpen(false);
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setProfileOpen(false);
    }
    document.addEventListener("mousedown", closeProfile);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeProfile);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  useEffect(() => {
    if (!connected) setProfileOpen(false);
  }, [connected]);

  useEffect(() => {
    if (!checkedAuth || !connected || !getBusinessId()) { setLoading(false); return; }
    setLoading(true);
    Promise.all([
      apiFetch(`/context/${getBusinessId()}`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
      apiFetch(`/kpis/sales/${getBusinessId()}`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
      apiFetch(`/anomalies/${getBusinessId()}?days=30&limit=5`).then((r) => (r.ok ? r.json() : [])),
    ]).then(([a, b, c]) => { setContext(a); setKpis(b); setAnomalies(c); setLive(true); }).catch((err) => {
      if (err instanceof ApiAuthError) { clearSession(); setUser(null); setConnected(false); return; }
      setContext(DEMO_CONTEXT); setLive(false);
    }).finally(() => setLoading(false));
  }, [checkedAuth, connected, dataVersion]);

  const revenue = useMemo(() => context?.evidence?.find((e) => e.metric === "revenue"), [context]);
  const businessName = useMemo(() => user?.business?.name || context?.entities?.find((entity) => entity.entity_type?.toLowerCase() === "business")?.label || "Business workspace", [user, context]);
  const find = (...n: string[]) => kpis.find((k) => n.some((x) => k.name.toLowerCase().includes(x)) && k.period !== "all_time");
  const totalRevenue = kpis.find((k) => k.name === "total_revenue");
  const totalInvoices = kpis.find((k) => k.name === "total_invoice_count");
  const rk = find("revenue"), ak = find("average", "aov");
  const revenueChange = rk?.change ?? (revenue?.metadata?.change != null ? revenue.metadata.change * 100 : null);
  const prioritySignals = (context?.signals || []).filter((s) => isPrioritySeverity(String(s.severity || "")));
  const positiveSignals = (context?.signals || []).filter((s) => isPositiveSeverity(String(s.severity || "")));
  const highSignals = prioritySignals;
  const health = highSignals.length >= 2 ? "Needs attention" : highSignals.length === 1 ? "Watch closely" : "On track";
  const healthText = health === "Needs attention" ? "A few issues deserve attention today." : health === "Watch closely" ? "Performance is mixed. Review the highlighted signals." : "No major warning signals are currently visible.";
  const healthIcon = health === "Needs attention" ? "alert" : health === "Watch closely" ? "pulse" : "check";
  const healthTone = health === "Needs attention" ? "danger" : health === "Watch closely" ? "amber" : "success";

  function explainMetric(id: string) { const reasoning = buildMetricReasoning(id, kpis, context || {}); if (reasoning) setSelectedReasoning(reasoning); }
  function explainHealth() { setSelectedReasoning(buildHealthReasoning(context || {}, health)); }

  async function runQuestion(q: string) {
    if (!q.trim()) return;
    setAsking(true); setAnswer(""); setError("");
    if (!live) { setTimeout(() => { setAnswer(demoAnswer(q)); setAsking(false); }, 300); return; }
    try {
      const r = await apiFetch(`/agent/${getBusinessId()}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
      if (!r.ok) throw Error(`Agent returned ${r.status}`);
      setAnswer((await r.json()).answer);
    } catch (x) {
      if (x instanceof ApiAuthError) { clearSession(); setUser(null); setConnected(false); return; }
      setError(x instanceof Error ? x.message : "Unable to reach Business Brain");
    } finally { setAsking(false); }
  }

  function ask(e: FormEvent) { e.preventDefault(); runQuestion(question); }
  function logout() { setProfileOpen(false); clearSession(); setUser(null); setConnected(false); setAnswer(""); setQuestion(""); setError(""); }

  if (checkedAuth && !connected) return <main className="shell"><header className="header"><div className="brand"><span className="brandMark"><Icon name="sparkle" className="icon" /></span><div><span className="eyebrow">BUSINESS BRAIN</span><h1>Your business, understood.</h1></div></div></header><ConnectGate onConnected={() => { setProfileOpen(false); setConnected(true); }} /></main>;

  const navGroups = [
    { label: "OVERVIEW", items: [{ id: "overview", label: "Dashboard", icon: "sparkle" as IconName }] },
    { label: "PERFORMANCE", items: [
      { id: "sales", label: "Sales Performance", icon: "trend" as IconName },
      { id: "customers", label: "Customers", icon: "invoice" as IconName },
    ]},
    { label: "BUSINESS", items: [
      { id: "financials", label: "Financials", icon: "wallet" as IconName },
      { id: "operations", label: "Operations", icon: "receipt" as IconName },
    ]},
    { label: "INTELLIGENCE", items: [
      { id: "insights", label: "Business Insights", icon: "sparkle" as IconName },
      { id: "reports", label: "Reports", icon: "trend" as IconName },
    ]},
    { label: "DATA", items: [{ id: "imports", label: "Data & Imports", icon: "arrow" as IconName }] },
  ];

  function renderSection() {
    if (activeSection === "overview") return <>
      <section className="dashboardIntro"><div><span className="eyebrow">OVERVIEW</span><h2>Good morning, {user?.username || "there"}.</h2><p>{businessName} · Here's the current picture of your business.</p></div><div className="freshStatus"><span className={`freshDot ${live ? "live" : ""}`} /> {loading ? "Refreshing data" : live ? "Data is up to date" : "Using sample data"}</div></section>
      <section className="dashboardSection"><div className="sectionHeading sectionHeadingLarge"><span>BUSINESS HEALTH</span><small>At-a-glance signals that deserve your attention</small></div><div className="healthLiteGrid">
        <div className={`healthLiteMain tone-${healthTone}`} onClick={explainHealth} role="button" tabIndex={0}><div className="healthLiteIcon"><Icon name={healthIcon} className="icon" /></div><div><span className="eyebrow">CURRENT STATUS</span><h3>{health}</h3><p>{healthText}</p></div><span className="cardArrow">→</span></div>
        <Metric label="Priority concerns" value={String(highSignals.length)} change="" note="signals requiring review" icon="alert" tone="danger" onClick={() => setActiveSection("insights")} />
        <Metric label="Positive / notable signals" value={String(positiveSignals.length)} change="" note="positive or informational movements" icon="check" tone="success" onClick={() => setActiveSection("insights")} />
      </div></section>
      <section className="dashboardSection"><div className="sectionHeading sectionHeadingLarge"><span>BUSINESS OVERVIEW</span><small>Core numbers from your imported business data</small></div><div className="metrics">
        <Metric label="Total Revenue" value={money(totalRevenue?.value ?? revenue?.value)} change="" note="all imported data" icon="wallet" onClick={() => explainMetric("total-revenue")} />
        <Metric label="Total Invoices" value={totalInvoices?.value ?? "—"} change="" note="all imported data" icon="invoice" onClick={() => explainMetric("total-invoices")} />
        <Metric label="Current Month Revenue" value={money(rk?.value)} change={pct(revenueChange)} note="vs previous month" icon="trend" tone={revenueChange == null ? "primary" : Number(revenueChange) < 0 ? "danger" : "success"} onClick={() => explainMetric("current-month-revenue")} />
        <Metric label="Average Invoice Value" value={money(ak?.value)} change={pct(ak?.change)} note="current month" icon="receipt" tone="amber" onClick={() => explainMetric("average-invoice-value")} />
      </div></section>
      <section className="dashboardSection"><div className="sectionHeading sectionHeadingLarge"><span>SALES PERFORMANCE</span><small>Revenue movement and commercial momentum</small></div><div className="salesPreview"><RevenueTrend /></div></section>
    </>;

    if (activeSection === "sales") return <section className="contentSection"><SectionTitle title="SALES PERFORMANCE" subtitle="Revenue movement and commercial momentum" /><div className="salesPreview"><RevenueTrend /><PerformanceTables dataVersion={dataVersion} /></div></section>;
    if (activeSection === "customers") return <section className="contentSection"><SectionTitle title="CUSTOMERS" subtitle="Customer contribution, activity and follow-up intelligence" /><PerformanceTables section="customers" dataVersion={dataVersion} /></section>;
    if (activeSection === "financials") return <section className="contentSection"><SectionTitle title="FINANCIALS" subtitle="Profitability, margins, cash position and receivables" /><div className="statGrid"><MarginIntelligence onExplain={setSelectedReasoning} /><ReceivablesIntelligence onExplain={setSelectedReasoning} /></div></section>;
    if (activeSection === "operations") return <section className="contentSection"><SectionTitle title="OPERATIONS" subtitle="Inventory health and operational intelligence" /><InventoryIntelligence onExplain={setSelectedReasoning} /></section>;
    if (activeSection === "insights") return <section className="contentSection"><SectionTitle title="BUSINESS INSIGHTS" subtitle="Signals, anomalies and recommended actions" /><div className="insightColumns">
      <section className="card"><div className="cardTitle"><b>Management attention</b><small>Highest-priority signals</small></div>{[...(context?.signals || [])].sort((a, b) => severityRank(String(a.severity || "")) - severityRank(String(b.severity || ""))).slice(0, 5).map((s, i) => { const sev = severityIcon(String(s.severity || "")); return <div className="signal" key={i}><span className={`iconChip sm tone-${sev.tone}`}><Icon name={sev.icon} className="icon" /></span><div className="signalBody"><div className="signalTop"><b>{String(s.title || s.name || "Business signal")}</b><span className={`tag ${isPrioritySeverity(String(s.severity || "")) ? "danger" : isPositiveSeverity(String(s.severity || "")) ? "good" : "warning"}`}>{String(s.severity || "REVIEW").toUpperCase()}</span></div><p>{String(s.message || s.description || "Review this signal.")}</p></div></div>; })}{!(context?.signals?.length) && <div className="insightEmpty"><span className="iconChip sm tone-success"><Icon name="check" className="icon" /></span><div><b>No priority signals detected</b><p>Business Brain isn't currently seeing anything requiring attention.</p></div></div>}</section>
      <section className="card"><div className="cardTitle"><b>Recommended actions</b><small>What to consider next</small></div>{context?.recommendations?.map((r, i) => <div className="signal" key={i}><div className="actionNo">{i + 1}</div><div className="signalBody"><b>{String(r.title || r.name || "Recommendation")}</b><p>{String(r.description || r.message || "Evidence-backed action available.")}</p></div></div>)}{!(context?.recommendations?.length) && <div className="insightEmpty"><span className="iconChip sm tone-success"><Icon name="check" className="icon" /></span><div><b>No recommended actions</b><p>There are no evidence-backed actions to review right now.</p></div></div>}</section>
    </div>{anomalies.length > 0 && <section className="card anomalyCard"><div className="cardTitle"><b>Exceptions</b><small>Unusual movements worth investigating</small></div>{anomalies.map((a, i) => <div className="anomaly" key={i}><span className={`iconChip sm tone-${a.severity === "high" ? "danger" : "amber"}`}><Icon name="alert" className="icon" /></span><div className="signalBody"><div className="signalTop"><b>{a.name}</b><span className={`tag ${a.severity === "high" ? "danger" : "warning"}`}>{a.severity.toUpperCase()}</span></div><p>Revenue {a.change_pct >= 0 ? "increased" : "decreased"} <strong>{Math.abs(a.change_pct).toFixed(0)}%</strong> versus the prior period.</p></div></div>)}</section>}</section>;
    if (activeSection === "reports") return <section className="contentSection"><SectionTitle title="REPORTS" subtitle="Reporting and analysis workspace" /><div className="card reportCard"><Icon name="trend" className="reportIcon" /><div><b>Detailed reporting</b><p>Review the business data and performance views. Report exports can be added here as the reporting layer grows.</p></div></section>;
    return <section className="contentSection"><SectionTitle title="DATA & IMPORTS" subtitle="Upload, validate and commit business data without leaving the dashboard" /><ImportWorkspace businessName={businessName} onImported={() => setDataVersion((v) => v + 1)} onDone={() => setActiveSection("overview")} /></section>;
  }

  return <main className="shell appShell">
    <aside className="appSidebar">
      <div className="sidebarTop"><div className="sidebarBrand"><span className="brandMark"><Icon name="sparkle" className="icon" /></span><div className="sidebarBrandText"><span className="eyebrow">BUSINESS BRAIN</span><strong>{businessName}</strong></div></div></div>
      <nav className="sidebarNav">{navGroups.map((group) => <div className="navGroup" key={group.label}><span className="navGroupLabel">{group.label}</span>{group.items.map((item) => <button key={item.id} className={`navItem ${activeSection === item.id ? "active" : ""}`} onClick={() => setActiveSection(item.id)}><span className="navIcon"><Icon name={item.icon} className="icon" /></span><span className="navLabel">{item.label}</span></button>)}</div>)}</nav>
      <div className="sidebarBottom"><button className="sidebarAsk" onClick={() => setChatOpen(true)} title="Ask Business Brain"><Icon name="chat" className="icon" /><span className="navLabel">Ask Business Brain</span></button></div>
    </aside>

    <div className="appMain">
      <header className="header dashboardHeader"><div className="pageContext"><span className="pageContextEyebrow">{navGroups.flatMap((group) => group.items).find((item) => item.id === activeSection)?.label ?? "Dashboard"}</span><span className="pageContextSub">Business performance and decision support</span></div><div className="headerRight"><span className={`status ${loading ? "loading" : live ? "live" : "demo"}`}><span className="statusDot" /> {loading ? "Updating…" : live ? "Live data" : "Demo mode"}</span><div className="profileWrap" ref={profileRef}><button type="button" className={`profileButton ${profileOpen ? "open" : ""}`} onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen}><span className="avatar"><Icon name="user" className="icon" /></span><span className="profileName">{user?.username || "User"}</span><span className="profileChevron">⌄</span></button>{profileOpen && <div className="profileMenu"><div className="profileMenuHead"><strong>{user?.username || "User"}</strong><span>{businessName}</span></div><button type="button" className="profileLogout" onClick={logout}>Log out</button></div>}</div></div></header>
      {!live && !loading && <div className="demoBanner"><strong>DEMO MODE</strong><span>Sample business data · safe for testing</span></div>}
      <div className="pageContent">{renderSection()}</div>
    </div>

    <button className="chatLauncher" onClick={() => setChatOpen(true)} aria-label="Ask Business Brain"><Icon name="chat" className="icon" /><span>Ask Business Brain</span></button>
    {chatOpen && <div className="chatOverlay" role="dialog" aria-modal="true"><div className="chatWindow"><div className="chatHeader"><div><span className="eyebrow">BUSINESS BRAIN</span><h3>Ask your business</h3><p>Ask a question and get an evidence-based answer.</p></div><button className="chatClose" onClick={() => setChatOpen(false)} aria-label="Close">×</button></div><div className="chatBody">{answer ? <div className="response chatResponse"><strong>Business Brain {live ? "· Live" : "· Demo"}</strong><p>{answer}</p></div> : <div className="chatEmpty"><span className="iconChip"><Icon name="sparkle" className="icon" /></span><b>What would you like to know?</b><p>Try asking about sales, revenue, customers or business health.</p></div>}{error && <div className="errorBox">{error}</div>}</div><form className="chatForm" onSubmit={ask}><input autoFocus value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g. Why did my sales fall?" disabled={asking} /><button disabled={asking || !question.trim()}>{asking ? "Thinking…" : "Ask"}</button></form></div></div>}
    <DashboardReasoningOverlay reasoning={selectedReasoning} onClose={() => setSelectedReasoning(null)} />
  </main>;
}

function ImportWorkspace({ businessName, onImported, onDone }: { businessName: string; onImported: () => void; onDone: () => void }) {
  const [files, setFiles] = useState<File[]>([]);
  const [preview, setPreview] = useState<any | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  function applyFiles(selected: File[]) {
    const accepted = selected.filter((file) => /\.(csv|xlsx?|xls)$/i.test(file.name));
    setFiles(accepted);
    setPreview(null);
    setResult(null);
    setError(accepted.length === selected.length ? "" : "Only CSV, XLSX or XLS files can be uploaded.");
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    applyFiles(Array.from(event.target.files || []));
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragging(false);
    applyFiles(Array.from(event.dataTransfer.files || []));
  }

  async function send(path: "preview" | "record-run") {
    if (!files.length) throw new Error("Choose at least one CSV or Excel file first.");
    const businessId = getBusinessId();
    if (!businessId) throw new Error("Your business session is missing. Please sign in again.");
    const form = new FormData(); files.forEach((selectedFile) => form.append("files", selectedFile));
    const response = await apiFetch(`/ingestion/${path}/${businessId}`, { method: "POST", body: form });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Import service returned ${response.status}`);
    return data;
  }
  async function previewFile() {
    setBusy(true); setError(""); setResult(null);
    try { setPreview(await send("preview")); } catch (e) { setError(e instanceof ApiAuthError ? "Your session has expired. Please sign in again." : e instanceof Error ? e.message : "Unable to preview files"); } finally { setBusy(false); }
  }
  async function importFile() {
    setBusy(true); setError("");
    try { const imported = await send("record-run"); setResult(imported); onImported(); } catch (e) { setError(e instanceof ApiAuthError ? "Your session has expired. Please sign in again." : e instanceof Error ? e.message : "Unable to import files"); } finally { setBusy(false); }
  }
  return <div className="importWorkspace">
    <section className="card importCard">
      <div className="importCardHead"><div><span className="eyebrow">DATA & IMPORTS</span><h3>Bring your sales data into Business Brain</h3><p>Upload one or more Tally CSV or Excel exports. We’ll validate everything before anything is committed.</p></div><span className="status">Workspace · {businessName}</span></div>
      <div className={`uploadZone ${dragging ? "dragging" : ""}`} onClick={() => document.getElementById("businessBrainFileInput")?.click()} onDragEnter={(event) => { event.preventDefault(); event.stopPropagation(); setDragging(true); }} onDragOver={(event) => { event.preventDefault(); event.stopPropagation(); setDragging(true); }} onDragLeave={(event) => { event.preventDefault(); event.stopPropagation(); if (event.currentTarget === event.target) setDragging(false); }} onDrop={handleDrop} role="button" tabIndex={0} aria-label="Upload sales files">
        <input id="businessBrainFileInput" className="uploadInput" type="file" multiple accept=".csv,.xlsx,.xls" onClick={(event) => { event.stopPropagation(); event.currentTarget.value = ""; }} onChange={chooseFile} />
        <div className="uploadIcon"><Icon name="arrow" className="icon" /></div>
        <div className="uploadCopy"><strong>{dragging ? "Release to add your sales files" : "Drop your sales files here"}</strong><span>or click to browse from your computer</span><small>CSV, XLSX or XLS · Multiple files supported</small></div>
        <span className="uploadBrowse">Choose files</span>
      </div>
      {files.length > 0 && <div className="selectedFiles">{files.map((selectedFile) => <span className="selectedFile" key={`${selectedFile.name}-${selectedFile.size}`}>{selectedFile.name} · {(selectedFile.size / 1024).toFixed(1)} KB</span>)}</div>}
      <div className="actions"><button onClick={previewFile} disabled={busy || files.length === 0}>{busy ? "Checking…" : "Preview & Validate"}</button></div>
    </section>
    {error && <div className="errorBox">{error}</div>}
    {preview && !result && <section className="card resultCard"><span className="eyebrow">VALIDATION PREVIEW</span><h3>{preview.file_count} file{preview.file_count === 1 ? "" : "s"} ready to import</h3><div className="metrics"><Metric label="Rows read" value={String(preview.rows_read)} change="" note="" icon="invoice" /><Metric label="Accepted" value={String(preview.rows_accepted)} change="" note="" icon="check" /><Metric label="Rejected" value={String(preview.rows_rejected)} change="" note="" icon="alert" tone="danger" /></div><div className="filePreviewList">{preview.files?.map((filePreview: any, i: number) => <div className="filePreview" key={`${filePreview.source}-${i}`}><div><strong>{filePreview.source}</strong><small>{filePreview.rows_read} rows · {filePreview.rows_accepted} accepted · {filePreview.rows_rejected} rejected</small></div>{filePreview.mapping?.length > 0 && <div className="issues compact"><b>Detected columns</b>{filePreview.mapping.map((m: any, j: number) => <span key={j}><strong>{m.canonical}</strong> ← {m.source} · {Math.round(m.confidence * 100)}%</span>)}</div>}{filePreview.issues?.length > 0 && <div className="issues"><b>Validation issues</b>{filePreview.issues.slice(0, 20).map((issue: any, j: number) => <p key={j}>Row {issue.row ?? "—"} · {issue.column ?? "file"}: {issue.message ?? "Validation issue"}</p>)}</div>}</div>)}</div><button onClick={importFile} disabled={busy || preview.rows_accepted === 0}>{busy ? "Importing…" : "Import accepted rows →"}</button></section>}
    {result && <section className="card resultCard success"><span className="eyebrow">IMPORT COMPLETE</span><h3>Data committed successfully.</h3><div className="importSummary"><span className="importSummaryItem"><strong>{result.file_count || 0}</strong><small>file{result.file_count === 1 ? "" : "s"} imported</small></span><span className="importSummaryItem"><strong>{result.sales_created?.toLocaleString?.() || 0}</strong><small>new records</small></span><span className="importSummaryItem"><strong>{result.sales_reconciled?.toLocaleString?.() || 0}</strong><small>updated</small></span><span className="importSummaryItem"><strong>{result.rows_rejected || 0}</strong><small>rejected</small></span></div><div className="importVerification"><span className="importStat"><small>Revenue after import</small><strong>{money(result.total_revenue_after_import)}</strong></span><span className="importStat"><small>Invoices after import</small><strong>{result.total_invoice_count_after_import ?? "—"}</strong></span></div><button className="dashboardReturnButton" onClick={onDone}>← Back to Dashboard</button></section>}
  </div>;
}

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return <div className="sectionHeading sectionHeadingLarge contentTitle"><span>{title}</span><small>{subtitle}</small></div>;
}

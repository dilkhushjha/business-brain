"use client";

import Icon from "./Icons";

type InsightContext = {
  signals?: Array<Record<string, unknown>>;
  recommendations?: Array<Record<string, unknown>>;
  situations?: Array<Record<string, unknown>>;
};

type Anomaly = { name: string; change_pct: number; severity: string };
type Severity = "critical" | "warning" | "high" | "medium" | "info" | "positive" | "unknown";

const order: Severity[] = ["critical", "warning", "high", "medium", "info", "positive", "unknown"];

function severity(value: unknown): Severity {
  const v = String(value || "").trim().toLowerCase();
  return order.includes(v as Severity) ? v as Severity : "unknown";
}

function severityLabel(value: unknown) {
  const v = severity(value);
  if (v === "high") return "High";
  if (v === "unknown") return "Review";
  return v.charAt(0).toUpperCase() + v.slice(1);
}

function severityClass(value: unknown) {
  const v = severity(value);
  if (v === "critical" || v === "warning" || v === "high") return "critical";
  if (v === "positive") return "positive";
  if (v === "info") return "info";
  return "medium";
}

function signalText(signal: Record<string, unknown>) {
  return String(signal.message || signal.description || signal.recommended_next_step || "Review this signal and the supporting evidence.");
}

function evidenceText(signal: Record<string, unknown>) {
  const e = signal.evidence;
  if (!e || typeof e !== "object") return "";
  const entries = Object.entries(e as Record<string, unknown>).filter(([, value]) => value !== null && value !== undefined && value !== "");
  if (!entries.length) return "";
  return entries.slice(0, 2).map(([key, value]) => {
    const label = key.replaceAll("_", " ");
    return label + ": " + (typeof value === "object" ? JSON.stringify(value) : String(value));
  }).join(" · ");
}

export default function BusinessInsights({ context, anomalies }: { context: InsightContext | null; anomalies: Anomaly[] }) {
  const signals = [...(context?.signals || [])].sort((a, b) => order.indexOf(severity(a.severity)) - order.indexOf(severity(b.severity)));
  const critical = signals.filter((s) => severity(s.severity) === "critical").length;
  const warning = signals.filter((s) => ["warning", "high"].includes(severity(s.severity))).length;
  const info = signals.filter((s) => ["medium", "info"].includes(severity(s.severity))).length;
  const positive = signals.filter((s) => severity(s.severity) === "positive").length;
  const attention = critical + warning;
  const recommendations = context?.recommendations || [];

  return (
    <section className="contentSection businessInsightsPage">
      <div className="insightsHero">
        <div>
          <span className="eyebrow">BUSINESS INSIGHTS</span>
          <h2>What needs your attention?</h2>
          <p>Signals from your business data, ordered by urgency so you can move from what happened to what to do next.</p>
        </div>
        <div className={"insightsHealth " + (attention ? "needsAttention" : "clear")}>
          <strong>{attention}</strong>
          <span>{attention === 1 ? "priority signal" : "priority signals"}</span>
        </div>
      </div>

      {(context?.situations || []).length > 0 && <section className="businessSituations">
        <div className="situationsHead">
          <div><span className="eyebrow">CROSS-DOMAIN INTELLIGENCE</span><h3>Business situations</h3><p>Related signals that point to the same underlying business issue.</p></div>
          <span className="insightCount">{context?.situations?.length || 0}</span>
        </div>
        <div className="situationsGrid">
          {(context?.situations || []).slice(0, 4).map((s, i) => {
            const sev = severity(s.severity);
            const evidence = s.evidence && typeof s.evidence === "object" ? Object.entries(s.evidence as Record<string, unknown>).filter(([, v]) => v !== null && v !== undefined && v !== "").slice(0, 2).map(([k, v]) => k.replaceAll("_", " ") + ": " + (typeof v === "object" ? JSON.stringify(v) : String(v))).join(" · ") : "";
            return <article className={"situationCard situation-" + severityClass(sev)} key={String(s.code || i)}>
              <div className="situationTop"><span className="insightSignalMetric">{String(s.code || "Situation").replaceAll("_", " ")}</span><span className="insightSeverity">{severityLabel(sev)}</span></div>
              <h4>{String(s.title || "Business situation")}</h4>
              <p>{String(s.explanation || "Related business signals require review together.")}</p>
              {evidence && <div className="situationEvidence"><b>Evidence</b><span>{evidence}</span></div>}
              {s.recommended_next_step && <div className="situationAction"><b>Investigate</b><span>{String(s.recommended_next_step)}</span></div>}
              {s.confidence !== undefined && <small>Confidence {Math.round(Number(s.confidence) * 100)}%</small>}
            </article>;
          })}
        </div>
      </section>}

      <div className="insightSummaryBar">
        <div><b>{critical}</b><span>Critical</span></div>
        <div><b>{warning}</b><span>Warnings</span></div>
        <div><b>{info}</b><span>Info</span></div>
        <div><b>{positive}</b><span>Positive</span></div>
        <div className="insightSummaryNote"><span>Data status</span><b>Live business data</b></div>
      </div>

      <div className="insightLayout">
        <main className="insightFeed">
          <div className="insightSectionHead">
            <div><h3>Signals</h3><span>{signals.length} detected · highest priority first</span></div>
          </div>

          {signals.length ? signals.map((s, i) => {
            const sev = severity(s.severity);
            const evidence = evidenceText(s);
            return (
              <article className={"insightSignal severity-" + severityClass(sev)} key={String(s.code || i)}>
                <div className="insightSignalRail"><span>{i + 1}</span></div>
                <div className="insightSignalMain">
                  <div className="insightSignalTop">
                    <div>
                      <span className="insightSignalMetric">{String(s.metric || "Business signal")}</span>
                      <h4>{String(s.title || s.name || "Business signal")}</h4>
                    </div>
                    <span className="insightSeverity">{severityLabel(sev)}</span>
                  </div>
                  <p>{signalText(s)}</p>
                  {evidence && <div className="insightEvidence"><b>Evidence</b><span>{evidence}</span></div>}
                  {s.recommended_next_step && <div className="insightNext"><b>Next</b><span>{String(s.recommended_next_step)}</span></div>}
                </div>
              </article>
            );
          }) : (
            <div className="insightBlank"><Icon name="check" className="icon" /><div><b>No active signals</b><p>Business Brain is not detecting a material issue from the current data.</p></div></div>
          )}
        </main>

        <aside className="insightRail">
          <section className="insightSideCard">
            <div className="insightSideHead"><div><span className="eyebrow">DECISION SUPPORT</span><h3>Recommended actions</h3></div><span className="insightCount">{recommendations.length}</span></div>
            {recommendations.length ? recommendations.slice(0, 5).map((r, i) => (
              <div className="recommendationItem" key={String(r.code || i)}>
                <span className="recommendationNo">{i + 1}</span>
                <div><b>{String(r.title || r.name || "Recommended action")}</b><p>{String(r.rationale || r.description || r.message || "Evidence-backed action available.")}</p></div>
              </div>
            )) : <div className="insightSideEmpty">No evidence-backed actions right now.</div>}
          </section>

          {anomalies.length > 0 && <section className="insightSideCard">
            <div className="insightSideHead"><div><span className="eyebrow">EXCEPTIONS</span><h3>Unusual movements</h3></div><span className="insightCount">{anomalies.length}</span></div>
            {anomalies.slice(0, 5).map((a, i) => (
              <div className="exceptionItem" key={i}>
                <div><b>{a.name}</b><span className={a.change_pct >= 0 ? "exceptionUp" : "exceptionDown"}>{a.change_pct >= 0 ? "▲" : "▼"} {Math.abs(a.change_pct).toFixed(0)}%</span></div>
                <small>{a.severity}</small>
              </div>
            ))}
          </section>}
        </aside>
      </div>
    </section>
  );
}

export type ReasoningEvidence = {
  label: string;
  value: string;
  detail?: string;
};

export type ReasoningPayload = {
  title: string;
  value: string;
  change?: string;
  context: string;
  why: string;
  implication: string;
  evidence?: ReasoningEvidence[];
};

export type BusinessContext = {
  evidence?: Array<{
    metric?: string;
    value?: string;
    metadata?: { change?: number };
  }>;
  signals?: Array<Record<string, unknown>>;
  recommendations?: Array<Record<string, unknown>>;
};

type KPI = {
  name: string;
  value: string | null;
  change?: string | null;
  period?: string;
};

const percent = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === "") return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? `${n >= 0 ? "+" : ""}${n.toFixed(0)}%` : undefined;
};

const money = (value: string | null | undefined) => {
  if (value == null || value === "") return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 10_000_000) return `₹${(n / 10_000_000).toFixed(2)}Cr`;
  if (Math.abs(n) >= 100_000) return `₹${(n / 100_000).toFixed(2)}L`;
  if (Math.abs(n) >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
};

const findKpi = (kpis: KPI[], ...names: string[]) =>
  kpis.find((kpi) => kpi.period !== "all_time" && names.some((name) => kpi.name.toLowerCase().includes(name)));

export function buildMetricReasoning(
  id: string,
  kpis: KPI[],
  context: BusinessContext,
): ReasoningPayload | null {
  const evidence = context.evidence || [];
  const revenueEvidence = evidence.find((item) => item.metric === "revenue");
  const revenueKpi = findKpi(kpis, "revenue");
  const aovKpi = findKpi(kpis, "average", "aov");
  const revenueChange = revenueKpi?.change ??
    (revenueEvidence?.metadata?.change != null ? revenueEvidence.metadata.change * 100 : undefined);

  switch (id) {
    case "total-revenue": {
      const kpi = kpis.find((item) => item.name === "total_revenue");
      return {
        title: "Total Revenue",
        value: money(kpi?.value ?? revenueEvidence?.value),
        context: "All imported sales data",
        why: "Cumulative revenue represented by the canonical sales records currently stored for this business.",
        implication: "This is a scale indicator, not a period-performance measure. Use Current Month Revenue to understand movement.",
        evidence: [
          { label: "Source", value: "Canonical sales records", detail: "Business Brain's data layer" },
          { label: "Scope", value: "All imported data" },
        ],
      };
    }
    case "total-invoices": {
      const kpi = kpis.find((item) => item.name === "total_invoice_count");
      return {
        title: "Total Invoices",
        value: kpi?.value ?? "—",
        context: "All imported sales data",
        why: "Count of invoice-level sales represented in the business data.",
        implication: "Read this together with revenue and average invoice value to understand transaction volume and order size.",
        evidence: [
          { label: "Source", value: "Invoice-level sales" },
          { label: "Duplicate handling", value: "Reconciled", detail: "Repeated exports do not simply create duplicate invoices." },
        ],
      };
    }
    case "current-month-revenue":
      return {
        title: "Current Month Revenue",
        value: money(revenueKpi?.value ?? revenueEvidence?.value),
        change: percent(revenueChange),
        context: "Current period vs previous comparable period",
        why: revenueChange == null
          ? "Current-period revenue is compared with the previous comparable period."
          : `Revenue moved ${Number(revenueChange) >= 0 ? "up" : "down"} ${Math.abs(Number(revenueChange)).toFixed(0)}%. This establishes a performance movement, not its cause.`,
        implication: "Investigate the customers and products contributing to the movement before deciding what action is needed.",
        evidence: revenueEvidence ? [
          { label: "Revenue evidence", value: money(revenueEvidence.value) },
          ...(revenueEvidence.metadata?.change != null ? [{ label: "Observed change", value: percent(revenueEvidence.metadata.change * 100) || "—" }] : []),
        ] : undefined,
      };
    case "average-invoice-value":
      return {
        title: "Average Invoice Value",
        value: money(aovKpi?.value),
        change: percent(aovKpi?.change),
        context: "Current month",
        why: "Average invoice value is calculated from invoice-level sales totals in the canonical data layer.",
        implication: "A movement can reflect order size, pricing, product mix, or customer mix. Read it alongside revenue and invoice count.",
      };
    default:
      return null;
  }
}

export function buildHealthReasoning(context: BusinessContext, status: string): ReasoningPayload {
  const signals = context.signals || [];
  const high = signals.filter((signal) => signal.severity === "high").length;
  const positive = signals.filter((signal) => signal.severity === "positive").length;
  return {
    title: "Business Health",
    value: status,
    context: `${high} priority concern${high === 1 ? "" : "s"} · ${positive} positive signal${positive === 1 ? "" : "s"}`,
    why: high
      ? `Business Brain currently detects ${high} high-priority signal${high === 1 ? "" : "s"}. The health verdict summarizes those detected signals rather than inventing a separate score.`
      : "No high-priority warning signals are currently detected in the available business data.",
    implication: "Use Management Attention to inspect the underlying signals and evidence before taking action.",
    evidence: signals.slice(0, 3).map((signal) => ({
      label: String(signal.title || signal.name || "Signal"),
      value: String(signal.severity || "REVIEW").toUpperCase(),
      detail: String(signal.message || signal.description || ""),
    })),
  };
}

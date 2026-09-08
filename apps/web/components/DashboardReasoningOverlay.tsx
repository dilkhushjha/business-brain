"use client";

import { useEffect, useState } from "react";
import styles from "./DashboardReasoningOverlay.module.css";

type Reasoning = {
  title: string;
  value: string;
  summary: string;
  details: string[];
};

function buildReasoning(target: HTMLElement): Reasoning {
  const label = target.querySelector(".metricLabel")?.textContent?.trim() ||
    target.querySelector("h3")?.textContent?.trim() ||
    target.querySelector(".signalTop b")?.textContent?.trim() ||
    target.querySelector("b")?.textContent?.trim() || "Business insight";
  const value = target.querySelector("strong")?.textContent?.trim() || "";
  const note = target.querySelector(".metricNote")?.textContent?.trim() || "";
  const change = target.querySelector(".delta")?.textContent?.trim() || "";
  const paragraph = target.querySelector("p")?.textContent?.trim() || "";

  if (target.classList.contains("healthPanel")) {
    return {
      title: "Business health",
      value: target.querySelector("h3")?.textContent?.trim() || "Current status",
      summary: target.querySelector("p")?.textContent?.trim() || "Health is based on the signals currently detected in the business data.",
      details: [
        "Priority concerns are counted from high-severity business signals.",
        "Positive signals are considered alongside warning signals to avoid a one-sided health score.",
        "This is a decision-support indicator, not a financial or accounting statement.",
      ],
    };
  }

  if (label.toLowerCase().includes("current month revenue")) {
    return {
      title: label,
      value,
      summary: change ? `The current-month revenue movement is ${change} ${note ? `(${note})` : ""}.` : "This card shows revenue for the current reporting period.",
      details: [
        "The value comes from the canonical sales data used by Business Brain.",
        "The change compares the current period with the previous comparable period.",
        "Use the Sales Performance section below to investigate which customers or products contributed to the movement.",
      ],
    };
  }

  if (label.toLowerCase().includes("average invoice")) {
    return {
      title: label,
      value,
      summary: change ? `Average invoice value moved ${change} ${note ? `in the ${note}` : "versus the comparable period"}.` : "This is the average value of invoices in the selected period.",
      details: [
        "Calculated from invoice-level sales totals rather than an LLM estimate.",
        "A falling average invoice value can indicate smaller baskets, lower pricing, or a change in customer mix.",
        "A rising value can indicate larger baskets, pricing changes, or a shift toward higher-value customers.",
      ],
    };
  }

  if (label.toLowerCase().includes("total revenue")) {
    return {
      title: label,
      value,
      summary: "This is the cumulative revenue represented by the imported business data.",
      details: [
        "The card uses the canonical sales records stored for this business.",
        "It is intentionally labelled as all imported data, so it should not be read as a monthly KPI.",
        "Use Current Month Revenue for period-over-period movement.",
      ],
    };
  }

  if (label.toLowerCase().includes("total invoices")) {
    return {
      title: label,
      value,
      summary: "This is the number of invoice-level sales represented by the imported data.",
      details: [
        "Repeated exports are reconciled at invoice level to avoid counting the same invoice twice.",
        "The value reflects imported canonical sales records for the business.",
      ],
    };
  }

  return {
    title: label,
    value,
    summary: paragraph || "This card summarizes a business signal or metric derived from the data available to Business Brain.",
    details: [
      note ? `Reporting context: ${note}.` : "The value is derived from canonical business data.",
      change ? `Observed movement: ${change}.` : "No period-over-period movement is shown on this card.",
      "Open the relevant section below to investigate the underlying customers, products, transactions, or signals.",
    ],
  };
}

export default function DashboardReasoningOverlay() {
  const [reasoning, setReasoning] = useState<Reasoning | null>(null);

  useEffect(() => {
    const selectors = [
      ".metric",
      ".healthPanel",
      ".signalCard .signal",
      ".actionCard .signal",
      ".anomalyCard .anomaly",
    ];

    const elements = Array.from(document.querySelectorAll<HTMLElement>(selectors.join(",")));
    const cleanups = elements.map((element) => {
      element.setAttribute("role", "button");
      element.setAttribute("tabindex", "0");
      element.setAttribute("aria-label", `View reasoning for ${element.querySelector(".metricLabel")?.textContent?.trim() || element.querySelector("h3")?.textContent?.trim() || "this business insight"}`);
      element.style.cursor = "pointer";
      element.style.transition = "box-shadow .15s ease, transform .15s ease";

      const open = () => setReasoning(buildReasoning(element));
      const keydown = (event: KeyboardEvent) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      };
      const enter = () => {
        element.style.transform = "translateY(-1px)";
        element.style.boxShadow = "0 8px 24px rgba(16,24,40,.09)";
      };
      const leave = () => {
        element.style.transform = "";
        element.style.boxShadow = "";
      };
      element.addEventListener("click", open);
      element.addEventListener("keydown", keydown);
      element.addEventListener("mouseenter", enter);
      element.addEventListener("mouseleave", leave);
      return () => {
        element.removeEventListener("click", open);
        element.removeEventListener("keydown", keydown);
        element.removeEventListener("mouseenter", enter);
        element.removeEventListener("mouseleave", leave);
        element.style.cursor = "";
        element.style.transition = "";
        element.style.transform = "";
        element.style.boxShadow = "";
      };
    });

    return () => cleanups.forEach((cleanup) => cleanup());
  });

  if (!reasoning) return null;

  return (
    <div className={styles.backdrop} role="presentation" onMouseDown={() => setReasoning(null)}>
      <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="reasoning-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className={styles.close} type="button" onClick={() => setReasoning(null)} aria-label="Close reasoning">×</button>
        <span className={styles.eyebrow}>BUSINESS BRAIN · REASONING</span>
        <h2 id="reasoning-title">{reasoning.title}</h2>
        {reasoning.value && <div className={styles.value}>{reasoning.value}</div>}
        <p className={styles.summary}>{reasoning.summary}</p>
        <div className={styles.section}>
          <span className={styles.sectionLabel}>HOW TO READ THIS</span>
          <ul>
            {reasoning.details.map((detail) => <li key={detail}>{detail}</li>)}
          </ul>
        </div>
        <div className={styles.footer}>Numbers come from the business data layer; reasoning is presented as decision support, not as a replacement for accounting records.</div>
      </section>
    </div>
  );
}

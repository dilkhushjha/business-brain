"use client";

import { useEffect, useState } from "react";
import styles from "./DashboardReasoningOverlay.module.css";

type Reasoning = {
  title: string;
  value: string;
  change?: string;
  context: string;
  why: string;
  implication: string;
};

function readMetric(element: HTMLElement): Reasoning {
  const label = element.querySelector(".metricLabel")?.textContent?.trim() || "Business metric";
  const value = element.querySelector("strong")?.textContent?.trim() || "—";
  const change = element.querySelector(".delta")?.textContent?.trim() || undefined;
  const note = element.querySelector(".metricNote")?.textContent?.trim() || "current reporting data";
  const key = label.toLowerCase();

  if (key === "total revenue") return { title: label, value, context: "All imported sales data", why: "This is the cumulative revenue represented by the sales records currently stored for this business.", implication: "Use it as a scale indicator. For performance movement, use Current Month Revenue rather than this all-time figure." };
  if (key === "total invoices") return { title: label, value, context: "All imported sales data", why: "Invoices are represented at invoice level, so repeated exports do not simply create another copy of the same invoice.", implication: "This helps you understand transaction volume and gives context to average invoice value." };
  if (key === "current month revenue") return { title: label, value, change, context: "Compared with the previous month", why: change ? `Revenue is ${change} versus the previous month. The movement is a signal to investigate, not an explanation by itself.` : "The current reporting period is being compared with the previous comparable period.", implication: "If revenue is falling, drill into the customers and products contributing most to the change before deciding what to do." };
  if (key === "average invoice value") return { title: label, value, change, context: "Current month", why: change ? `Average invoice value is ${change} versus the comparable period.` : "This represents the typical value of an invoice in the current month.", implication: "A change can come from order size, pricing, product mix, or customer mix. It is most useful when read alongside revenue and invoice count." };

  return { title: label, value, change, context: note, why: "This metric is derived from the business data available to Business Brain.", implication: "Open the relevant intelligence section to investigate the records behind this number." };
}

function readHealth(element: HTMLElement): Reasoning {
  const status = element.querySelector("h3")?.textContent?.trim() || "Business health";
  const description = element.querySelector("p")?.textContent?.trim() || "";
  return { title: "Business health", value: status, context: "Current detected signals", why: description || "The health verdict summarizes the warning and positive signals currently visible in the business data.", implication: "Treat this as a prioritization aid. The signals below are the evidence you should investigate before taking action." };
}

export default function DashboardReasoningOverlay() {
  const [reasoning, setReasoning] = useState<Reasoning | null>(null);

  useEffect(() => {
    const open = (event: MouseEvent) => {
      const target = (event.target as HTMLElement).closest<HTMLElement>(".metric, .healthPanel");
      if (!target) return;
      setReasoning(target.classList.contains("metric") ? readMetric(target) : readHealth(target));
    };
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setReasoning(null);
      if ((event.key === "Enter" || event.key === " ") && document.activeElement instanceof HTMLElement) {
        const target = document.activeElement.closest<HTMLElement>(".metric, .healthPanel");
        if (!target) return;
        event.preventDefault();
        setReasoning(target.classList.contains("metric") ? readMetric(target) : readHealth(target));
      }
    };
    const markInteractive = () => document.querySelectorAll<HTMLElement>(".metric, .healthPanel").forEach((element) => {
      element.setAttribute("role", "button");
      element.setAttribute("tabindex", "0");
      element.setAttribute("aria-label", `View reasoning for ${element.querySelector(".metricLabel")?.textContent?.trim() || element.querySelector("h3")?.textContent?.trim() || "this metric"}`);
    });

    document.addEventListener("click", open);
    document.addEventListener("keydown", keydown);
    markInteractive();
    const observer = new MutationObserver(markInteractive);
    observer.observe(document.body, { childList: true, subtree: true });
    return () => { document.removeEventListener("click", open); document.removeEventListener("keydown", keydown); observer.disconnect(); };
  }, []);

  if (!reasoning) return null;

  return (
    <div className={styles.backdrop} onMouseDown={() => setReasoning(null)}>
      <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="reasoning-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className={styles.close} type="button" onClick={() => setReasoning(null)} aria-label="Close">×</button>
        <div className={styles.header}>
          <span className={styles.eyebrow}>WHY THIS NUMBER?</span>
          <h2 id="reasoning-title">{reasoning.title}</h2>
          <div className={styles.value}>{reasoning.value}</div>
          {reasoning.change && <span className={styles.change}>{reasoning.change}</span>}
        </div>
        <div className={styles.context}>{reasoning.context}</div>
        <div className={styles.reasonBlock}><span>WHAT IT TELLS YOU</span><p>{reasoning.why}</p></div>
        <div className={styles.reasonBlock}><span>WHY IT MATTERS</span><p>{reasoning.implication}</p></div>
        <div className={styles.footer}>Business Brain uses the underlying business data as the source of truth. This explanation helps interpret the metric; it does not invent a cause that the data has not established.</div>
      </section>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import styles from "./DashboardReasoningOverlay.module.css";

export type ReasoningEvidence = { label: string; value: string; detail?: string };
export type ReasoningPayload = { title: string; value: string; change?: string; context: string; why: string; implication: string; evidence?: ReasoningEvidence[] };

export default function DashboardReasoningOverlay({ reasoning, onClose }: { reasoning: ReasoningPayload | null; onClose: () => void }) {
  useEffect(() => {
    if (!reasoning) return;
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [reasoning, onClose]);

  if (!reasoning) return null;
  return (
    <div className={styles.backdrop} onMouseDown={onClose}>
      <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="reasoning-title" onMouseDown={(event) => event.stopPropagation()}>
        <button className={styles.close} type="button" onClick={onClose} aria-label="Close">×</button>
        <div className={styles.header}>
          <span className={styles.eyebrow}>WHY THIS NUMBER?</span>
          <h2 id="reasoning-title">{reasoning.title}</h2>
          <div className={styles.value}>{reasoning.value}</div>
          {reasoning.change && <span className={styles.change}>{reasoning.change}</span>}
        </div>
        <div className={styles.context}>{reasoning.context}</div>
        <div className={styles.reasonBlock}><span>WHAT IT TELLS YOU</span><p>{reasoning.why}</p></div>
        {reasoning.evidence?.length ? <div className={styles.reasonBlock}><span>UNDERLYING EVIDENCE</span><ul className={styles.evidenceList}>{reasoning.evidence.map((item) => <li key={`${item.label}-${item.value}`}><strong>{item.label}</strong><b>{item.value}</b>{item.detail && <small>{item.detail}</small>}</li>)}</ul></div> : null}
        <div className={styles.reasonBlock}><span>WHY IT MATTERS</span><p>{reasoning.implication}</p></div>
        <div className={styles.footer}>Business Brain uses the underlying business data as the source of truth. This explanation interprets the evidence; it does not invent a cause that the data has not established.</div>
      </section>
    </div>
  );
}

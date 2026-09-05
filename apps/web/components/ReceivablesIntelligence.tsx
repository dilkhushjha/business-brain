"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";
import { apiFetch, getBusinessId } from "../lib/api";


const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

type S = { outstanding: number; overdue: number; overdue_pct: number; buckets: Record<string, number> };
type C = { name: string; overdue_amount: number; days_overdue: number };

export default function ReceivablesIntelligence() {
    const [s, setS] = useState<S | null>(null);
    const [c, setC] = useState<C[]>([]);

    useEffect(() => {
        Promise.all([
            apiFetch(`/receivables/${getBusinessId()}/summary`).then((r) => (r.ok ? r.json() : null)),
            apiFetch(`/receivables/${getBusinessId()}/overdue?limit=5`).then((r) => (r.ok ? r.json() : [])),
        ]).then(([a, b]) => { setS(a); setC(b); }).catch(() => { });
    }, []);

    if (!s || !s.outstanding) return null;

    return (
        <section className="card">
            <div className="cardTitle">
                <span><Icon name="clock" className="icon" /></span>
                <h3>Receivables &amp; cash</h3>
                <small>Outstanding invoices</small>
            </div>
            <div className="marginStats">
                <div><span>Outstanding</span><b>{money(s.outstanding)}</b></div>
                <div><span>Overdue</span><b className={s.overdue > 0 ? "negative" : undefined}>{money(s.overdue)}</b></div>
                <div><span>Overdue share</span><b>{s.overdue_pct}%</b></div>
            </div>
            {c.length > 0 && (
                <div className="marginAlerts">
                    <strong>Customers needing collection</strong>
                    {c.map((x) => (
                        <div className="marginRow" key={x.name}>
                            <span>{x.name}</span>
                            <b>{money(x.overdue_amount)}</b>
                            <em>{x.days_overdue} days overdue</em>
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
}
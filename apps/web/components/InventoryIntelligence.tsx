"use client";
import { useEffect, useState } from "react";
import Icon from "./Icons";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "11111111-1111-1111-1111-111111111111";
const money = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

type Row = { name: string; units_sold: number; revenue: number; avg_daily_units: number; signal: string; recommended_review?: string | null };

export default function InventoryIntelligence() {
    const [r, setR] = useState<Row[]>([]);

    useEffect(() => {
        fetch(`${API}/inventory/${BUSINESS_ID}/signals?days=30&limit=5`).then((x) => (x.ok ? x.json() : [])).then(setR).catch(() => { });
    }, []);

    if (!r.length) return null;

    return (
        <section className="card">
            <div className="cardTitle">
                <span><Icon name="box" className="icon" /></span>
                <h3>Inventory signals</h3>
                <small>Based on recent sales velocity</small>
            </div>
            <div className="marginAlerts">
                {r.map((x) => (
                    <div className="marginRow" key={x.name}>
                        <span>{x.name}</span>
                        <b>{x.avg_daily_units.toFixed(1)}/day</b>
                        <em>
                            {x.signal === "fast_mover" ? <span className="tag good">FAST MOVER</span> : <span className="tag">NORMAL</span>} · {money(x.revenue)}
                        </em>
                    </div>
                ))}
            </div>
        </section>
    );
}
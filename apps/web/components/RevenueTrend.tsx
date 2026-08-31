"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

type Point = { date: string; revenue: number };

const money = (n: number) => {
  if (Math.abs(n) >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (Math.abs(n) >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (Math.abs(n) >= 1000) return `₹${(n / 1000).toFixed(0)}K`;
  return `₹${Math.round(n)}`;
};

export default function RevenueTrend() {
  const [points, setPoints] = useState<Point[]>([]);

  useEffect(() => {
    fetch(`${API}/trends/revenue/${BUSINESS_ID}?days=30`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setPoints(data.points ?? data ?? []))
      .catch(() => setPoints([]));
  }, []);

  if (!points.length) return null;

  const max = Math.max(...points.map((p) => p.revenue), 1);
  const min = Math.min(...points.map((p) => p.revenue), 0);
  const width = 720, height = 220, pad = 20;
  const range = Math.max(max - min, 1);
  const xAt = (i: number) => pad + (i / Math.max(points.length - 1, 1)) * (width - pad * 2);
  const yAt = (v: number) => height - pad - ((v - min) / range) * (height - pad * 2);

  const linePath = points.map((p, i) => `${i ? "L" : "M"}${xAt(i).toFixed(1)},${yAt(p.revenue).toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${xAt(points.length - 1).toFixed(1)},${height - pad} L${xAt(0).toFixed(1)},${height - pad} Z`;
  const gridLines = [0.25, 0.5, 0.75].map((f) => height - pad - f * (height - pad * 2));
  const last = points[points.length - 1];
  const first = points[0];
  const changePct = first.revenue ? ((last.revenue - first.revenue) / first.revenue) * 100 : 0;

  return (
    <section className="card trendCard">
      <div className="cardTitle">
        <span><Icon /></span>
        <h3>Revenue trend</h3>
        <small className={changePct >= 0 ? "positive" : "negative"}>{changePct >= 0 ? "▲" : "▼"} {Math.abs(changePct).toFixed(0)}% over period</small>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="30 day revenue trend" className="trendChart">
        <defs>
          <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>
        {gridLines.map((y, i) => <line key={i} x1={pad} x2={width - pad} y1={y} y2={y} className="trendGrid" />)}
        <path d={areaPath} fill="url(#revFill)" stroke="none" />
        <path d={linePath} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={xAt(points.length - 1)} cy={yAt(last.revenue)} r="4.5" fill="currentColor" stroke="#fff" strokeWidth="2" />
      </svg>
      <div className="trendLabels">
        <span>{first.date}</span>
        <span className="trendLast">{money(last.revenue)} on {last.date}</span>
      </div>
    </section>
  );
}

function Icon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M3 17l6-6 4 4 8-8M21 7h-6v6" />
    </svg>
  );
}
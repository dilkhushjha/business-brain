"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "demo";

type Point = { date: string; revenue: number };

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
  const width = 720, height = 220, pad = 20;
  const path = points.map((p, i) => {
    const x = pad + (i / Math.max(points.length - 1, 1)) * (width - pad * 2);
    const y = height - pad - (p.revenue / max) * (height - pad * 2);
    return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  return <section className="card trendCard">
    <div className="cardTitle"><span>↗</span><h3>Revenue trend</h3></div>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="30 day revenue trend" className="trendChart">
      <path d={path} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
    <div className="trendLabels"><span>{points[0].date}</span><span>{points[points.length - 1].date}</span></div>
  </section>;
}

"use client";

import { useEffect, useState } from "react";
import { apiFetch, getBusinessId } from "../lib/api";



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
    apiFetch(`/trends/revenue/${getBusinessId()}?days=30`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setPoints(data.points ?? data ?? []))
      .catch(() => setPoints([]));
  }, []);

  if (!points.length) return null;

  const rawMax = Math.max(...points.map((p) => p.revenue), 1);
  const rawMin = Math.min(...points.map((p) => p.revenue), 0);
  const width = 900, height = 210, padX = 18, padY = 18;
  const rawRange = Math.max(rawMax - rawMin, 1);
  const chartMin = Math.max(0, rawMin - rawRange * 0.08);
  const chartMax = rawMax + rawRange * 0.08;
  const range = Math.max(chartMax - chartMin, 1);
  const xAt = (i: number) => padX + (i / Math.max(points.length - 1, 1)) * (width - padX * 2);
  const yAt = (v: number) => height - padY - ((v - chartMin) / range) * (height - padY * 2);

  const linePath = points.map((p, i) => `${i ? "L" : "M"}${xAt(i).toFixed(1)},${yAt(p.revenue).toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${xAt(points.length - 1).toFixed(1)},${height - padY} L${xAt(0).toFixed(1)},${height - padY} Z`;
  const gridLines = [0.25, 0.5, 0.75].map((f) => height - padY - f * (height - padY * 2));
  const formatDate = (value: string) => {
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  };
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
      <div className="trendChartWrap">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="30 day revenue trend" className="trendChart">
        <defs>
          <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>
        {gridLines.map((y, i) => <line key={i} x1={padX} x2={width - padX} y1={y} y2={y} className="trendGrid" />)}
        <path d={areaPath} fill="url(#revFill)" stroke="none" />
        <path d={linePath} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <line x1={xAt(points.length - 1)} x2={xAt(points.length - 1)} y1={padY} y2={height - padY} className="trendHoverLine" />
        <circle cx={xAt(points.length - 1)} cy={yAt(last.revenue)} r="4.5" fill="currentColor" stroke="#fff" strokeWidth="2" />
        {points.map((point, i) => <circle key={point.date + i} cx={xAt(i)} cy={yAt(point.revenue)} r="9" className="trendPointHit"><title>{formatDate(point.date)} · {money(point.revenue)}</title></circle>)}
        </svg>
        <div className="trendDates">{points.map((point, i) => {
          const step = Math.ceil(points.length / 6);
          const showLabel = points.length <= 8 || i === 0 || i === points.length - 1 || i % step === 0;
          return showLabel ? <span key={point.date + i} style={{ left: (xAt(i) / width) * 100 + "%" }}>{formatDate(point.date)}</span> : null;
        })}</div>
      </div>
      <div className="trendLabels">
        <span>{formatDate(first.date)}</span>
        <span className="trendLast">{money(last.revenue)} on {formatDate(last.date)}</span>
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
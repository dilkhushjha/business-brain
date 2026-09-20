"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiFetch, getBusinessId } from "../lib/api";

type Point = { date: string; revenue: number };

const money = (n: number) => {
  if (Math.abs(n) >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (Math.abs(n) >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (Math.abs(n) >= 1000) return `₹${(n / 1000).toFixed(0)}K`;
  return `₹${Math.round(n)}`;
};

const formatDate = (value: string) => {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
};

function RevenueHover({ active, payload }: { active?: boolean; payload?: Array<{ payload: Point }> }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="revenueHover">
      <strong>{formatDate(point.date)}</strong>
      <span>{money(point.revenue)}</span>
    </div>
  );
}

export default function RevenueTrend() {
  const [points, setPoints] = useState<Point[]>([]);

  useEffect(() => {
    apiFetch(`/trends/revenue/${getBusinessId()}?days=30`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setPoints(data.points ?? data ?? []))
      .catch(() => setPoints([]));
  }, []);

  if (!points.length) return null;

  const first = points[0];
  const last = points[points.length - 1];
  const changePct = first.revenue ? ((last.revenue - first.revenue) / first.revenue) * 100 : 0;

  return (
    <section className="card trendCard">
      <div className="cardTitle">
        <span><Icon /></span>
        <h3>Revenue trend</h3>
        <small className={changePct >= 0 ? "positive" : "negative"}>
          {changePct >= 0 ? "▲" : "▼"} {Math.abs(changePct).toFixed(0)}% over period
        </small>
      </div>

      <div className="trendChartWrap">
        <ResponsiveContainer width="100%" height={230}>
          <LineChart data={points} margin={{ top: 12, right: 4, bottom: 8, left: 4 }}>
            <CartesianGrid vertical={false} className="trendGrid" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              minTickGap={22}
              padding={{ left: 0, right: 0 }}
            />
            <YAxis
              tickFormatter={money}
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              width={48}
              domain={[0, "auto"]}
            />
            <Tooltip
              content={<RevenueHover />}
              cursor={{ strokeDasharray: "4 4" }}
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="currentColor"
              strokeWidth={2.5}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
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
      <path d="M3 17l6-6 4-4 8-8M21 7h-6v6" />
    </svg>
  );
}

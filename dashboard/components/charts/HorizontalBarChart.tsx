"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

export type FormatType = "currency" | "percent" | "number" | "pp";

interface HorizontalBarChartProps {
  data: { name: string; value: number }[];
  color?: string;
  format?: FormatType;
}

const COLORS = ["#dfa832", "#c78a1e", "#a56d18", "#7e5217", "#59381b", "#3b2412"];

function makeFormatter(format?: FormatType): (v: number) => string {
  switch (format) {
    case "currency":
      return (v) =>
        new Intl.NumberFormat("en-GB", {
          style: "currency",
          currency: "GBP",
          notation: "compact",
          maximumFractionDigits: 1,
        }).format(v);
    case "percent":
      return (v) => `${(v * 100).toFixed(1)}%`;
    case "number":
      return (v) =>
        new Intl.NumberFormat("en-GB", {
          notation: "compact",
          maximumFractionDigits: 1,
        }).format(v);
    case "pp":
      return (v) => `${(v * 100).toFixed(1)}pp`;
    default:
      return (v) => v.toFixed(0);
  }
}

export default function HorizontalBarChart({
  data,
  color,
  format,
}: HorizontalBarChartProps) {
  const formatter = makeFormatter(format);
  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 40)}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e31" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={formatter}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={110}
        />
        <Tooltip
          formatter={(v: number) => [formatter(v)]}
          contentStyle={{ background: "#161625", border: "1px solid #1e1e31", borderRadius: 8, fontSize: 12, color: "#e2e8f0" }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#e2e8f0" }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={28}>
          {data.map((_, i) => (
            <Cell key={i} fill={color ?? COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

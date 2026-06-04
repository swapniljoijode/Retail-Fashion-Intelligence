"use client";

import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

type FormatType = "currency" | "percent" | "number" | "pp";

interface DonutChartProps {
  data: { name: string; value: number }[];
  format?: FormatType;
}

const COLORS = ["#dfa832", "#8b5cf6", "#06b6d4", "#ec4899", "#22c55e", "#f59e0b"];

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

export default function DonutChart({ data, format }: DonutChartProps) {
  const formatter = makeFormatter(format);
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={3}
          dataKey="value"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(v: number) => [formatter(v)]}
          contentStyle={{ background: "#161625", border: "1px solid #1e1e31", borderRadius: 8, fontSize: 12, color: "#e2e8f0" }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#e2e8f0" }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => (
            <span style={{ color: "#94a3b8", fontSize: 11 }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

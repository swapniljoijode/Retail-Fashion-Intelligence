"use client";

import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

interface InventoryTrendChartProps {
  data: { label: string; avg_units_on_hand: number; stockout_rate: number }[];
}

export default function InventoryTrendChart({ data }: InventoryTrendChartProps) {
  // Sample every 4th week to reduce visual noise
  const sampled = data.filter((_, i) => i % 4 === 0);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={sampled} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e31" />
        <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis
          yAxisId="stock"
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={50}
        />
        <YAxis
          yAxisId="rate"
          orientation="right"
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={45}
        />
        <Tooltip
          formatter={(v: number, name: string) =>
            name === "Stockout Rate"
              ? [`${(v * 100).toFixed(1)}%`, name]
              : [v.toFixed(0), name]
          }
          contentStyle={{ background: "#161625", border: "1px solid #1e1e31", borderRadius: 8, fontSize: 12, color: "#e2e8f0" }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#e2e8f0" }}
        />
        <Legend
          formatter={(value) => (
            <span style={{ color: "#94a3b8", fontSize: 11 }}>{value}</span>
          )}
        />
        <Area
          yAxisId="stock"
          type="monotone"
          dataKey="avg_units_on_hand"
          stroke="#06b6d4"
          strokeWidth={2}
          fill="#06b6d420"
          name="Avg Units On Hand"
        />
        <Line
          yAxisId="rate"
          type="monotone"
          dataKey="stockout_rate"
          stroke="#ef4444"
          strokeWidth={2}
          dot={false}
          name="Stockout Rate"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

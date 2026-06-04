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

interface HorizontalBarChartProps {
  data: { name: string; value: number }[];
  color?: string;
  formatter?: (v: number) => string;
}

const COLORS = ["#dfa832", "#c78a1e", "#a56d18", "#7e5217", "#59381b", "#3b2412"];

export default function HorizontalBarChart({
  data,
  color,
  formatter = (v) => v.toFixed(0),
}: HorizontalBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 40)}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e31" horizontal={false} />
        <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={formatter} />
        <YAxis type="category" dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} width={110} />
        <Tooltip
          formatter={(v: number) => [formatter(v)]}
          contentStyle={{ background: "#161625", border: "1px solid #1e1e31", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#e2e8f0" }}
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

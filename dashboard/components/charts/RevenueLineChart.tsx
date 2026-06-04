"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface RevenueLineChartProps {
  data: { label: string; gross_revenue: number; net_revenue: number }[];
}

const fmt = (v: number) =>
  new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    notation: "compact",
    maximumFractionDigits: 0,
  }).format(v);

export default function RevenueLineChart({ data }: RevenueLineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
        <defs>
          <linearGradient id="grad-gross" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#dfa832" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#dfa832" stopOpacity={0.0} />
          </linearGradient>
          <linearGradient id="grad-net" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e31" />
        <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={fmt} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
        <Tooltip
          formatter={(v: number, name: string) => [fmt(v), name === "gross_revenue" ? "Gross Revenue" : "Net Revenue"]}
          contentStyle={{ background: "#161625", border: "1px solid #1e1e31", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#e2e8f0" }}
        />
        <Area type="monotone" dataKey="gross_revenue" stroke="#dfa832" strokeWidth={2} fill="url(#grad-gross)" name="gross_revenue" />
        <Area type="monotone" dataKey="net_revenue"   stroke="#8b5cf6" strokeWidth={2} fill="url(#grad-net)"   name="net_revenue" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

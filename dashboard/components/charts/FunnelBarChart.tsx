"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

const STAGE_LABELS: Record<string, string> = {
  page_view:      "Page View",
  product_view:   "Product View",
  add_to_cart:    "Add to Cart",
  checkout_start: "Checkout",
  purchase:       "Purchase",
  abandon_cart:   "Abandoned",
};

const STAGE_ORDER = [
  "page_view", "product_view", "add_to_cart", "checkout_start", "purchase",
];

const STAGE_COLORS: Record<string, string> = {
  page_view:      "#dfa832",
  product_view:   "#c78a1e",
  add_to_cart:    "#a56d18",
  checkout_start: "#7e5217",
  purchase:       "#22c55e",
  abandon_cart:   "#ef4444",
};

interface FunnelBarChartProps {
  data: { event_type: string; sessions: number }[];
}

export default function FunnelBarChart({ data }: FunnelBarChartProps) {
  const sorted = STAGE_ORDER.map((et) => {
    const row = data.find((d) => d.event_type === et);
    return { name: STAGE_LABELS[et] ?? et, value: row?.sessions ?? 0, et };
  });

  const fmt = (v: number) =>
    new Intl.NumberFormat("en-GB", { notation: "compact" }).format(v);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={sorted} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
        <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={fmt} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} width={50} />
        <Tooltip
          formatter={(v: number) => [fmt(v), "Sessions"]}
          contentStyle={{ background: "#161625", border: "1px solid #1e1e31", borderRadius: 8, fontSize: 12, color: "#e2e8f0" }}
          labelStyle={{ color: "#e2e8f0" }}
          itemStyle={{ color: "#e2e8f0" }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {sorted.map((row, i) => (
            <Cell key={i} fill={STAGE_COLORS[row.et] ?? "#dfa832"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

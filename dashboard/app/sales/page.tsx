import { getSalesData, getOverviewData, fmtCurrency, fmtNumber, fmtPct } from "@/lib/data";
import KpiCard from "@/components/KpiCard";
import PageHeader from "@/components/PageHeader";
import ChartCard from "@/components/ChartCard";
import RevenueLineChart from "@/components/charts/RevenueLineChart";
import HorizontalBarChart from "@/components/charts/HorizontalBarChart";

export default function SalesPage() {
  const sales = getSalesData();
  const overview = getOverviewData();
  const kpis = overview.kpis;

  const fmtC  = (v: number) => fmtCurrency(v, true);

  // Channel chart data
  const channelData = sales.by_channel.map((r) => ({
    name: r.channel_name,
    value: r.gross_revenue,
  }));

  // Category chart data
  const categoryData = sales.by_category.map((r) => ({
    name: r.category,
    value: r.gross_revenue,
  }));

  // Margin by category
  const marginData = sales.by_category.map((r) => ({
    name: r.category,
    value: r.gross_margin_pct,
  }));

  return (
    <div>
      <PageHeader
        title="Sales"
        subtitle="Revenue, margin, and order performance across all channels and categories."
        decision="Where is revenue growing, and which categories and channels are driving it?"
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          label="Gross Revenue"
          value={fmtCurrency(kpis.gross_revenue)}
          sub="YTD"
          highlight
        />
        <KpiCard
          label="Net Revenue"
          value={fmtCurrency(kpis.net_revenue)}
          sub="after discounts"
        />
        <KpiCard
          label="Gross Margin"
          value={fmtPct(kpis.gross_margin_pct)}
          sub="net revenue basis"
        />
        <KpiCard
          label="Avg Order Value"
          value={fmtCurrency(kpis.aov)}
          sub={`${fmtNumber(kpis.total_orders)} orders`}
        />
      </div>

      {/* Revenue trend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <ChartCard
          title="Monthly Revenue Trend"
          subtitle="Gross vs Net Revenue — 2024"
          className="lg:col-span-2"
        >
          <RevenueLineChart data={sales.monthly_trend} />
        </ChartCard>

        <ChartCard title="Revenue by Channel" subtitle="Gross revenue split">
          <HorizontalBarChart data={channelData} format="currency" />
        </ChartCard>
      </div>

      {/* Category split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Revenue by Category" subtitle="Gross revenue ranking">
          <HorizontalBarChart data={categoryData} format="currency" />
        </ChartCard>

        <ChartCard title="Gross Margin % by Category" subtitle="Net revenue basis">
          <HorizontalBarChart
            data={marginData}
            color="#8b5cf6"
            format="percent"
          />
        </ChartCard>
      </div>

      {/* Top products table */}
      <ChartCard title="Top 10 Products by Revenue" subtitle="Current SKU versions only">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Product", "Category", "Brand", "Revenue", "Units", "Margin %"].map((h) => (
                  <th
                    key={h}
                    className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide"
                    style={{ color: "var(--muted)" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sales.top_products.map((p, i) => (
                <tr
                  key={i}
                  style={{ borderBottom: "1px solid var(--border)" }}
                  className="hover:bg-opacity-5"
                >
                  <td className="py-2.5 px-3" style={{ color: "var(--text)" }}>
                    {p.product_name}
                  </td>
                  <td className="py-2.5 px-3" style={{ color: "var(--muted)" }}>
                    {p.category}
                  </td>
                  <td className="py-2.5 px-3" style={{ color: "var(--muted)" }}>
                    {p.brand}
                  </td>
                  <td className="py-2.5 px-3 font-mono" style={{ color: "var(--brand-gold)" }}>
                    {fmtC(p.gross_revenue)}
                  </td>
                  <td className="py-2.5 px-3 font-mono" style={{ color: "var(--text)" }}>
                    {fmtNumber(p.units)}
                  </td>
                  <td className="py-2.5 px-3 font-mono" style={{ color: "var(--text)" }}>
                    {fmtPct(p.gross_margin_pct)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  );
}

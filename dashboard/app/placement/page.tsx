import { getPlacementData, fmtCurrency, fmtNumber, fmtPct } from "@/lib/data";
import KpiCard from "@/components/KpiCard";
import PageHeader from "@/components/PageHeader";
import ChartCard from "@/components/ChartCard";
import HorizontalBarChart from "@/components/charts/HorizontalBarChart";

export default function PlacementPage() {
  const pl = getPlacementData();

  const regionRevenueData = pl.by_region.map((r) => ({
    name: r.region,
    value: r.gross_revenue,
  }));

  const storeTypeData = pl.by_store_type.map((r) => ({
    name: r.store_type,
    value: r.gross_revenue,
  }));

  const regionStockoutData = pl.inventory_by_region.map((r) => ({
    name: r.region,
    value: r.stockout_rate,
  }));

  // Imbalance: positive = revenue share > stock share (under-stocked)
  const imbalanceData = pl.revenue_vs_stock_by_region.map((r) => ({
    name: r.region,
    value: r.revenue_stock_imbalance,
  }));

  const topRegion = pl.by_region[0];

  return (
    <div>
      <PageHeader
        title="Placement"
        subtitle="Regional revenue distribution, stock allocation, and imbalance signals."
        decision="Which regions are under-stocked relative to their revenue contribution?"
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          label="Top Region"
          value={topRegion?.region ?? "—"}
          sub={fmtCurrency(topRegion?.gross_revenue)}
          highlight
        />
        <KpiCard
          label="Stores"
          value={pl.by_region.reduce((s, r) => s + r.stores, 0).toString()}
          sub={`${pl.by_region.length} regions`}
        />
        <KpiCard
          label="Revenue per Store"
          value={fmtCurrency(topRegion?.revenue_per_store, true)}
          sub={`${topRegion?.region} leading`}
        />
        <KpiCard
          label="Largest Imbalance"
          value={pl.revenue_vs_stock_by_region[0]?.region ?? "—"}
          sub={`+${fmtPct(pl.revenue_vs_stock_by_region[0]?.revenue_stock_imbalance)} revenue over stock`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Revenue by Region" subtitle="Gross revenue — ranked">
          <HorizontalBarChart data={regionRevenueData} formatter={(v) => fmtCurrency(v, true)} />
        </ChartCard>

        <ChartCard title="Revenue by Store Type" subtitle="Gross revenue split">
          <HorizontalBarChart data={storeTypeData} formatter={(v) => fmtCurrency(v, true)} />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard
          title="Revenue vs Stock Imbalance"
          subtitle="Positive = region over-contributes revenue vs stock share (may need replenishment)"
        >
          <HorizontalBarChart
            data={imbalanceData}
            color="#f59e0b"
            formatter={(v) => `${(v * 100).toFixed(1)}pp`}
          />
        </ChartCard>

        <ChartCard title="Stockout Rate by Region">
          <HorizontalBarChart
            data={regionStockoutData}
            color="#ef4444"
            formatter={(v) => fmtPct(v)}
          />
        </ChartCard>
      </div>

      {/* Full region table */}
      <ChartCard title="Regional Summary">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Region", "Stores", "Revenue", "Units", "Rev/Store", "Rev Share", "Stock Share", "Imbalance"].map((h) => (
                  <th key={h} className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pl.revenue_vs_stock_by_region.map((r, i) => {
                const reg = pl.by_region.find((x) => x.region === r.region);
                return (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="py-2 px-3" style={{ color: "var(--text)" }}>{r.region}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--muted)" }}>{reg?.stores ?? "—"}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--brand-gold)" }}>{fmtCurrency(r.gross_revenue, true)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtNumber(reg?.units_sold ?? 0, true)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtCurrency(reg?.revenue_per_store ?? 0, true)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtPct(r.revenue_share)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtPct(r.stock_share)}</td>
                    <td
                      className="py-2 px-3 font-mono"
                      style={{ color: r.revenue_stock_imbalance > 0 ? "var(--negative)" : "var(--positive)" }}
                    >
                      {r.revenue_stock_imbalance > 0 ? "+" : ""}
                      {fmtPct(r.revenue_stock_imbalance)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  );
}

import { getPlanningData, fmtNumber, fmtPct } from "@/lib/data";
import KpiCard from "@/components/KpiCard";
import PageHeader from "@/components/PageHeader";
import ChartCard from "@/components/ChartCard";
import HorizontalBarChart from "@/components/charts/HorizontalBarChart";
import InventoryTrendChart from "@/components/charts/InventoryTrendChart";

export default function PlanningPage() {
  const plan = getPlanningData();

  const sellThroughData = plan.sell_through.map((r) => ({
    name: r.category,
    value: r.sell_through_rate ?? 0,
  }));

  const stockoutData = plan.stockout_by_category.map((r) => ({
    name: r.category,
    value: r.stockout_rate,
  }));

  const avgStockout = plan.weekly_inventory.length
    ? plan.weekly_inventory.reduce((s, r) => s + r.stockout_rate, 0) / plan.weekly_inventory.length
    : 0;

  const avgUnitsOnHand = plan.weekly_inventory.length
    ? plan.weekly_inventory.reduce((s, r) => s + r.avg_units_on_hand, 0) / plan.weekly_inventory.length
    : 0;

  return (
    <div>
      <PageHeader
        title="Product Planning"
        subtitle="Inventory health, sell-through, and stockout risk by category and store."
        decision="What to replenish now, what to hold, and where stockout risk is highest?"
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          label="Avg Stockout Rate"
          value={fmtPct(avgStockout)}
          sub="weekly average"
          highlight
        />
        <KpiCard
          label="Avg Units On Hand"
          value={fmtNumber(avgUnitsOnHand, true)}
          sub="across all stores"
        />
        <KpiCard
          label="Best Sell-Through"
          value={
            [...plan.sell_through].sort((a, b) => (b.sell_through_rate ?? 0) - (a.sell_through_rate ?? 0))[0]
              ?.category ?? "—"
          }
          sub={fmtPct(
            [...plan.sell_through].sort((a, b) => (b.sell_through_rate ?? 0) - (a.sell_through_rate ?? 0))[0]
              ?.sell_through_rate
          )}
        />
        <KpiCard
          label="Highest Risk Category"
          value={plan.stockout_by_category[0]?.category ?? "—"}
          sub={fmtPct(plan.stockout_by_category[0]?.stockout_rate)}
        />
      </div>

      <div className="mb-4">
        <ChartCard title="Inventory Level vs Stockout Rate" subtitle="Weekly trend — sampled every 4 weeks">
          <InventoryTrendChart data={plan.weekly_inventory} />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Sell-Through Rate by Category" subtitle="Units sold ÷ (units sold + avg stock)">
          <HorizontalBarChart
            data={sellThroughData}
            color="#22c55e"
            formatter={(v) => fmtPct(v)}
          />
        </ChartCard>

        <ChartCard title="Stockout Rate by Category" subtitle="% of product-store-days in stockout">
          <HorizontalBarChart
            data={stockoutData}
            color="#ef4444"
            formatter={(v) => fmtPct(v)}
          />
        </ChartCard>
      </div>

      <ChartCard title="Stockout Detail by Store Type and Region">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Store Type", "Region", "Stockout Rate", "Avg Units On Hand"].map((h) => (
                  <th key={h} className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {plan.stockout_by_store.map((r, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td className="py-2 px-3" style={{ color: "var(--text)" }}>{r.store_type}</td>
                  <td className="py-2 px-3" style={{ color: "var(--muted)" }}>{r.region}</td>
                  <td className="py-2 px-3 font-mono" style={{ color: r.stockout_rate > 0.1 ? "var(--negative)" : "var(--positive)" }}>
                    {fmtPct(r.stockout_rate)}
                  </td>
                  <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>
                    {fmtNumber(r.avg_units_on_hand, true)}
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

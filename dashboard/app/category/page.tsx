import { getCategoryData, fmtCurrency, fmtNumber, fmtPct } from "@/lib/data";
import KpiCard from "@/components/KpiCard";
import PageHeader from "@/components/PageHeader";
import ChartCard from "@/components/ChartCard";
import HorizontalBarChart from "@/components/charts/HorizontalBarChart";

export default function CategoryPage() {
  const cat = getCategoryData();

  const revenueData = cat.by_category.map((c) => ({
    name: c.category,
    value: c.gross_revenue,
  }));

  const marginData = cat.by_category.map((c) => ({
    name: c.category,
    value: c.gross_margin_pct,
  }));

  const markdownData = cat.markdown_by_category.map((c) => ({
    name: c.category,
    value: c.avg_markdown_depth,
  }));

  const totalRevenue = cat.by_category.reduce((s, c) => s + c.gross_revenue, 0);

  return (
    <div>
      <PageHeader
        title="Category Management"
        subtitle="Margin, markdown depth, and revenue contribution by category."
        decision="Which categories earn their floor space, and where is markdown deepest?"
      />

      {/* KPIs — top category */}
      {cat.by_category[0] && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <KpiCard
            label="Top Category"
            value={cat.by_category[0].category}
            sub={fmtCurrency(cat.by_category[0].gross_revenue)}
            highlight
          />
          <KpiCard
            label="Best Margin"
            value={
              [...cat.by_category].sort((a, b) => b.gross_margin_pct - a.gross_margin_pct)[0]?.category ?? "—"
            }
            sub={fmtPct(
              [...cat.by_category].sort((a, b) => b.gross_margin_pct - a.gross_margin_pct)[0]?.gross_margin_pct
            )}
          />
          <KpiCard
            label="Highest Markdown"
            value={
              [...cat.markdown_by_category].sort((a, b) => b.avg_markdown_depth - a.avg_markdown_depth)[0]?.category ?? "None"
            }
            sub={fmtPct(
              [...cat.markdown_by_category].sort((a, b) => b.avg_markdown_depth - a.avg_markdown_depth)[0]?.avg_markdown_depth
            )}
          />
          <KpiCard
            label="Categories"
            value={cat.by_category.length.toString()}
            sub={`${fmtCurrency(totalRevenue, true)} total revenue`}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Revenue by Category" subtitle="Gross revenue ranking">
          <HorizontalBarChart data={revenueData} format="currency" />
        </ChartCard>

        <ChartCard title="Gross Margin % by Category" subtitle="Net revenue basis">
          <HorizontalBarChart
            data={marginData}
            color="#8b5cf6"
            format="percent"
          />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Avg Markdown Depth by Category" subtitle="Clearance months (Jan, Jul, Aug)">
          <HorizontalBarChart
            data={markdownData}
            color="#ef4444"
            format="percent"
          />
        </ChartCard>

        <ChartCard title="Category Performance Summary">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Category", "Revenue", "Margin %", "Discount %", "Units"].map((h) => (
                    <th key={h} className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cat.by_category.map((c, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="py-2 px-3" style={{ color: "var(--text)" }}>{c.category}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--brand-gold)" }}>{fmtCurrency(c.gross_revenue, true)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtPct(c.gross_margin_pct)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtPct(c.discount_rate)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtNumber(c.units_sold)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </div>
    </div>
  );
}

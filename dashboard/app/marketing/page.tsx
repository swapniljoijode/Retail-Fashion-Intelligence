import { getMarketingData, getOverviewData, fmtNumber, fmtPct, fmtCurrency } from "@/lib/data";
import KpiCard from "@/components/KpiCard";
import PageHeader from "@/components/PageHeader";
import ChartCard from "@/components/ChartCard";
import HorizontalBarChart from "@/components/charts/HorizontalBarChart";
import FunnelBarChart from "@/components/charts/FunnelBarChart";
import DonutChart from "@/components/charts/DonutChart";

export default function MarketingPage() {
  const mkt = getMarketingData();
  const kpis = getOverviewData().kpis;

  const deviceData = mkt.by_device.map((d) => ({
    name: d.device_type,
    value: d.sessions,
  }));

  const returnData = mkt.returns_by_reason.map((r) => ({
    name: r.return_reason.replace("_", " "),
    value: r.returns,
  }));

  return (
    <div>
      <PageHeader
        title="Marketing"
        subtitle="Session conversion, digital channels, and returns analysis."
        decision="Which channels and devices convert, and what is driving returns?"
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard
          label="Total Sessions"
          value={fmtNumber(kpis.total_web_sessions, true)}
          highlight
        />
        <KpiCard
          label="Conversion Rate"
          value={fmtPct(kpis.web_conversion_rate)}
          sub="session → purchase"
        />
        <KpiCard
          label="Return Rate"
          value={fmtPct(kpis.return_rate_units)}
          sub="by units"
        />
        <KpiCard
          label="Refund Value"
          value={fmtCurrency(kpis.total_refund_value, true)}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Conversion Funnel" subtitle="Sessions reaching each event stage">
          <FunnelBarChart data={mkt.funnel} />
        </ChartCard>

        <ChartCard title="Sessions by Device" subtitle="Share of total web sessions">
          <DonutChart
            data={deviceData}
            formatter={(v) => fmtNumber(v, true)}
          />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Returns by Reason" subtitle="Total return count by reason code">
          <HorizontalBarChart data={returnData} color="#ef4444" />
        </ChartCard>

        <ChartCard title="Monthly Return Volume" subtitle="Returns and refund value over time">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Month", "Returns", "Units", "Refund Value"].map((h) => (
                    <th key={h} className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {mkt.returns_by_month.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td className="py-2 px-3" style={{ color: "var(--text)" }}>{r.label}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtNumber(r.returns)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--text)" }}>{fmtNumber(r.units_returned)}</td>
                    <td className="py-2 px-3 font-mono" style={{ color: "var(--negative)" }}>{fmtCurrency(r.refund_value)}</td>
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

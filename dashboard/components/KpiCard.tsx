interface KpiCardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: { pct: number; up: boolean } | null;
  highlight?: boolean;
}

export default function KpiCard({
  label,
  value,
  sub,
  trend,
  highlight = false,
}: KpiCardProps) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-2"
      style={{
        background: "var(--surface)",
        border: highlight
          ? "1px solid var(--brand-gold)"
          : "1px solid var(--border)",
      }}
    >
      <p className="text-xs font-medium uppercase tracking-wide" style={{ color: "var(--muted)" }}>
        {label}
      </p>

      <p className="text-2xl font-bold" style={{ color: "var(--text)" }}>
        {value}
      </p>

      <div className="flex items-center gap-2 min-h-[20px]">
        {trend != null && (
          <span
            className="text-xs font-semibold"
            style={{ color: trend.up ? "var(--positive)" : "var(--negative)" }}
          >
            {trend.up ? "▲" : "▼"} {Math.abs(trend.pct).toFixed(1)}%
          </span>
        )}
        {sub && (
          <span className="text-xs" style={{ color: "var(--muted)" }}>
            {sub}
          </span>
        )}
      </div>
    </div>
  );
}

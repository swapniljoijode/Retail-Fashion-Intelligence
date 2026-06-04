interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export default function ChartCard({ title, subtitle, children, className = "" }: ChartCardProps) {
  return (
    <div
      className={`rounded-xl p-5 ${className}`}
      style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
    >
      <div className="mb-4">
        <p className="text-sm font-semibold" style={{ color: "var(--text)" }}>
          {title}
        </p>
        {subtitle && (
          <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
            {subtitle}
          </p>
        )}
      </div>
      {children}
    </div>
  );
}

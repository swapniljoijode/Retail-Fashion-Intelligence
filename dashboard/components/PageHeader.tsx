interface PageHeaderProps {
  title: string;
  subtitle: string;
  decision?: string;
}

export default function PageHeader({ title, subtitle, decision }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>
        {title}
      </h1>
      <p className="text-sm" style={{ color: "var(--muted)" }}>
        {subtitle}
      </p>
      {decision && (
        <div
          className="mt-3 px-4 py-2 rounded-lg border-l-2 text-sm"
          style={{
            background: "var(--surface)",
            borderColor: "var(--brand-gold)",
            color: "var(--text)",
          }}
        >
          <span style={{ color: "var(--brand-gold)" }} className="font-semibold">
            Decision:{" "}
          </span>
          {decision}
        </div>
      )}
    </div>
  );
}

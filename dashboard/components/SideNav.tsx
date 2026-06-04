"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/sales",     label: "Sales",            icon: "💷" },
  { href: "/marketing", label: "Marketing",         icon: "📣" },
  { href: "/category",  label: "Category",          icon: "🏷️" },
  { href: "/planning",  label: "Product Planning",  icon: "📦" },
  { href: "/placement", label: "Placement",         icon: "🗺️" },
];

export default function SideNav() {
  const pathname = usePathname();

  return (
    <nav
      className="flex flex-col w-56 shrink-0 border-r"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      {/* Brand */}
      <div className="px-5 py-6 border-b" style={{ borderColor: "var(--border)" }}>
        <p
          className="text-xs font-semibold tracking-widest uppercase mb-1"
          style={{ color: "var(--brand-gold)" }}
        >
          Fashion Retail
        </p>
        <p className="text-lg font-bold" style={{ color: "var(--text)" }}>
          Intelligence
        </p>
      </div>

      {/* Links */}
      <div className="flex-1 py-4 space-y-1 px-3">
        {NAV_ITEMS.map(({ href, label, icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
              style={{
                background: active ? "var(--surface-2)" : "transparent",
                color: active ? "var(--brand-gold)" : "var(--muted)",
                borderLeft: active ? `2px solid var(--brand-gold)` : "2px solid transparent",
              }}
            >
              <span className="text-base">{icon}</span>
              {label}
            </Link>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t" style={{ borderColor: "var(--border)" }}>
        <p className="text-xs" style={{ color: "var(--muted)" }}>
          Medallion architecture
        </p>
        <p className="text-xs" style={{ color: "var(--muted)" }}>
          DuckDB · dbt · Airflow
        </p>
      </div>
    </nav>
  );
}

"use client";

import { useState } from "react";
import JSZip from "jszip";

const DATA_FILES = [
  { name: "overview.json",  label: "Overview KPIs"   },
  { name: "sales.json",     label: "Sales"            },
  { name: "marketing.json", label: "Marketing"        },
  { name: "category.json",  label: "Category"         },
  { name: "planning.json",  label: "Product Planning" },
  { name: "placement.json", label: "Placement"        },
];

const README = `Fashion Retail Intelligence Platform — Data Export
===================================================

Source:   https://github.com/swapniljoijode/Retail-Fashion-Intelligence
Model:    Star schema — medallion architecture (Bronze → Silver → Gold via dbt)
Warehouse: DuckDB (permanent shadow) + Snowflake (trial)
Generated: Synthetic data — Python (Faker, NumPy, pandas, pyarrow)

Files
-----
overview.json   KPI summary (gross revenue, net revenue, margin %, AOV, orders,
                web sessions, conversion rate, return rate, refund value)

sales.json      Monthly revenue trend, channel split, category split, top-10 products
                Columns: label, gross_revenue, net_revenue, channel_name, units,
                         gross_margin_pct, product_name, category, brand

marketing.json  Conversion funnel (sessions by event type), sessions by device,
                returns by reason, monthly return volume with refund values

category.json   Per-category: gross_revenue, net_revenue, gross_margin_pct,
                discount_rate, units_sold, avg_markdown_depth

planning.json   Weekly inventory trend (avg_units_on_hand, stockout_rate),
                sell-through rate by category, stockout rate by store type × region

placement.json  Revenue and stores by region and store type,
                inventory allocation metrics, revenue vs stock imbalance per region

Schema
------
Fact tables:     fct_sales, fct_inventory_snapshot, fct_returns,
                 fct_web_events, fct_markdown
Dimensions:      dim_product (SCD2), dim_store, dim_customer (SCD2),
                 dim_date, dim_channel, dim_promotion
`;

export default function DownloadDataButton() {
  const [loading, setLoading] = useState(false);

  async function handleDownload() {
    setLoading(true);
    try {
      const zip = new JSZip();
      zip.file("README.txt", README);
      const folder = zip.folder("data")!;

      await Promise.all(
        DATA_FILES.map(async ({ name }) => {
          const res = await fetch(`/data/${name}`);
          const text = await res.text();
          folder.file(name, text);
        })
      );

      const blob = await zip.generateAsync({ type: "blob", compression: "DEFLATE" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "fashion-retail-data.zip";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      title="Download all 6 domain JSON files as a ZIP"
      className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
      style={{
        background: "transparent",
        color: loading ? "var(--muted)" : "var(--muted)",
        border: "1px solid var(--border)",
        cursor: loading ? "not-allowed" : "pointer",
      }}
      onMouseEnter={(e) => {
        if (!loading) {
          (e.currentTarget as HTMLButtonElement).style.color = "var(--text)";
          (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--brand-gold)";
        }
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.color = "var(--muted)";
        (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)";
      }}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ flexShrink: 0 }}
      >
        {loading ? (
          <circle cx="12" cy="12" r="10" strokeDasharray="31.4" strokeDashoffset="10" />
        ) : (
          <>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </>
        )}
      </svg>
      {loading ? "Preparing…" : "Download Data"}
    </button>
  );
}

import { readFileSync } from "fs";
import { join } from "path";
import type {
  OverviewData,
  SalesData,
  MarketingData,
  CategoryData,
  PlanningData,
  PlacementData,
  ImagesData,
} from "./types";

function readJson<T>(name: string): T {
  const filePath = join(process.cwd(), "public", "data", `${name}.json`);
  return JSON.parse(readFileSync(filePath, "utf-8")) as T;
}

export const getOverviewData  = () => readJson<OverviewData>("overview");
export const getSalesData     = () => readJson<SalesData>("sales");
export const getMarketingData = () => readJson<MarketingData>("marketing");
export const getCategoryData  = () => readJson<CategoryData>("category");
export const getPlanningData  = () => readJson<PlanningData>("planning");
export const getPlacementData = () => readJson<PlacementData>("placement");
export const getImagesData    = () => readJson<ImagesData>("images");

// ── Formatting helpers ────────────────────────────────────────────────────────

export function fmtCurrency(n: number | null | undefined, compact = false): string {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    notation: compact ? "compact" : "standard",
    maximumFractionDigits: compact ? 1 : 0,
  }).format(n);
}

export function fmtNumber(n: number | null | undefined, compact = false): string {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-GB", {
    notation: compact ? "compact" : "standard",
    maximumFractionDigits: compact ? 1 : 0,
  }).format(n);
}

export function fmtPct(n: number | null | undefined, decimals = 1): string {
  if (n == null) return "—";
  return `${(n * 100).toFixed(decimals)}%`;
}

export function trend(current: number, previous: number): { pct: number; up: boolean } {
  const pct = previous === 0 ? 0 : ((current - previous) / Math.abs(previous)) * 100;
  return { pct, up: pct >= 0 };
}

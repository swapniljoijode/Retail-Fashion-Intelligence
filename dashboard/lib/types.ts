// ── Overview ──────────────────────────────────────────────────────────────────
export interface OverviewKpis {
  gross_revenue: number;
  net_revenue: number;
  total_cogs: number;
  total_gross_margin: number;
  gross_margin_pct: number;
  total_orders: number;
  total_units: number;
  aov: number;
  return_rate_units: number;
  total_units_returned: number;
  total_refund_value: number;
  stockout_rate: number;
  total_web_sessions: number;
  web_conversion_rate: number;
  unique_customers: number;
}

export interface MonthlyRevenue {
  year: number;
  month: number;
  label: string;
  gross_revenue: number;
  net_revenue: number;
  gross_margin: number;
  orders: number;
  units: number;
}

export interface OverviewData {
  generated_at: string;
  kpis: OverviewKpis;
  revenue_by_month: MonthlyRevenue[];
}

// ── Sales ─────────────────────────────────────────────────────────────────────
export interface SalesMonthlyRow {
  year: number;
  month: number;
  label: string;
  gross_revenue: number;
  net_revenue: number;
  discount_amount: number;
  gross_margin: number;
  gross_margin_pct: number;
  orders: number;
  units: number;
  aov: number;
  discount_rate: number;
}

export interface ChannelRow {
  channel_name: string;
  channel_type: string;
  gross_revenue: number;
  net_revenue: number;
  orders: number;
  units: number;
  revenue_share: number;
}

export interface CategorySalesRow {
  category: string;
  gross_revenue: number;
  net_revenue: number;
  gross_margin_pct: number;
  orders: number;
  units: number;
}

export interface TopProductRow {
  product_name: string;
  sku: string;
  category: string;
  brand: string;
  gross_revenue: number;
  units: number;
  gross_margin_pct: number;
}

export interface SalesData {
  monthly_trend: SalesMonthlyRow[];
  by_channel: ChannelRow[];
  by_category: CategorySalesRow[];
  top_products: TopProductRow[];
  by_promotion: { promotion_name: string; orders: number; gross_revenue: number; avg_discount_rate: number }[];
}

// ── Marketing ─────────────────────────────────────────────────────────────────
export interface SessionRow {
  year: number;
  month: number;
  label: string;
  sessions: number;
  conversions: number;
  conversion_rate: number;
}

export interface FunnelRow {
  event_type: string;
  events: number;
  sessions: number;
}

export interface DeviceRow {
  device_type: string;
  sessions: number;
  share: number;
}

export interface ReturnReasonRow {
  return_reason: string;
  returns: number;
  units_returned: number;
  refund_value: number;
}

export interface MarketingData {
  monthly_sessions: SessionRow[];
  funnel: FunnelRow[];
  by_device: DeviceRow[];
  returns_by_reason: ReturnReasonRow[];
  returns_by_month: { year: number; month: number; label: string; returns: number; units_returned: number; refund_value: number }[];
}

// ── Category ──────────────────────────────────────────────────────────────────
export interface CategoryRow {
  category: string;
  gross_revenue: number;
  net_revenue: number;
  gross_margin_pct: number;
  units_sold: number;
  discount_rate: number;
}

export interface MarkdownCategoryRow {
  category: string;
  avg_markdown_depth: number;
  units_on_markdown: number;
  revenue_on_markdown: number;
  markdown_events: number;
}

export interface CategoryData {
  by_category: CategoryRow[];
  markdown_by_category: MarkdownCategoryRow[];
  by_season: { season: string; retail_season: string; gross_revenue: number; gross_margin_pct: number; units_sold: number }[];
}

// ── Planning ──────────────────────────────────────────────────────────────────
export interface WeeklyInventoryRow {
  year: number;
  week_num: number;
  week_start: string;
  label: string;
  avg_units_on_hand: number;
  stockout_rate: number;
  units_in_transit: number;
}

export interface SellThroughRow {
  category: string;
  units_sold: number;
  avg_stock: number;
  sell_through_rate: number;
}

export interface StockoutCategoryRow {
  category: string;
  stockout_rate: number;
  stockout_days: number;
  total_days: number;
}

export interface PlanningData {
  weekly_inventory: WeeklyInventoryRow[];
  sell_through: SellThroughRow[];
  stockout_by_category: StockoutCategoryRow[];
  stockout_by_store: { store_type: string; region: string; stockout_rate: number; avg_units_on_hand: number }[];
}

// ── Product Images ────────────────────────────────────────────────────────────
export interface CategoryImage {
  pexels_id:    number | null;
  url:          string;
  alt:          string;
  photographer: string;
  pexels_url:   string;
  r2_key:       string | null;
}

export type ImagesData = Record<string, CategoryImage>;

// ── Placement ─────────────────────────────────────────────────────────────────
export interface RegionRow {
  region: string;
  stores: number;
  gross_revenue: number;
  net_revenue: number;
  units_sold: number;
  revenue_per_store: number;
}

export interface StoreTypeRow {
  store_type: string;
  size_band: string;
  stores: number;
  avg_sqft: number;
  gross_revenue: number;
  units_sold: number;
  revenue_per_store: number;
}

export interface PlacementData {
  by_region: RegionRow[];
  by_store_type: StoreTypeRow[];
  inventory_by_region: { region: string; avg_units_on_hand: number; stockout_rate: number; total_in_transit: number }[];
  revenue_vs_stock_by_region: { region: string; gross_revenue: number; revenue_share: number; avg_stock: number; stock_share: number; revenue_stock_imbalance: number }[];
}

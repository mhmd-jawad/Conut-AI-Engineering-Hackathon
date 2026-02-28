import axios, { AxiosError } from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

/* ───────────────────────── Health ───────────────────────── */
export interface HealthResponse {
  status: string;
  service?: string;
}

/* ───────────────────────── Chat ─────────────────────────── */
export interface ChatRequest {
  question: string; // backend expects "question", NOT "message"
}
export interface ChatResponse {
  intent: string;
  branch?: string | null;
  answer: string;
  confidence: number;
  elapsed_ms: number;
  data?: unknown;
  error?: string | null;
}

/* ──────────────────────── Combos ────────────────────────── */
export interface ComboRequest {
  branch: string;
  top_k?: number;
  include_modifiers?: boolean;
  min_support?: number;
  min_confidence?: number;
  min_lift?: number;
}
export interface ComboPair {
  item_a: string;
  item_b: string;
  support: number;
  confidence_a_to_b: number;
  confidence_b_to_a: number;
  lift: number;
  basket_count: number;
  avg_combo_revenue: number;
  price_a: number;
  price_b: number;
  individual_total: number;
  suggested_combo_price: number;
  savings: number;
}
export interface ComboResponse {
  branch: string;
  total_baskets: number;
  include_modifiers: boolean;
  recommendations: ComboPair[];
  explanation: string;
}

/* ─────────────────────── Forecast ───────────────────────── */
export interface ForecastRequest {
  branch: string;
  horizon_months?: number;
}
export interface HistoryPoint {
  month: string;
  total: number;
}
export interface MonthForecast {
  month: string;
  naive: number;
  wma: number;
  trend: number;
  ensemble: number;
}
export interface ForecastResponse {
  branch: string;
  horizon_months: number;
  trend: string;
  confidence: string; // "low", "medium", "low-medium", etc.
  demand_index?: number | null;
  avg_mom_growth_pct?: number | null;
  history: HistoryPoint[];
  forecasts: MonthForecast[];
  anomaly_notes?: string[] | null;
  explanation: string;
  error?: string | null;
}

/* ─────────────────────── Staffing ───────────────────────── */
export interface StaffingRequest {
  branch: string;
  shift: string;
}
export interface StaffingResponse {
  branch: string;
  shift: string;
  recommended_staff: number;
  scenarios: { low: number; base: number; high: number };
  confidence: string; // backend returns string like "medium"
  demand_factor: number;
  demand_trend: string;
  explanation: string;
}

/* ─────────────────────── Expansion ──────────────────────── */
export interface ExpansionRequest {
  branch: string;
}
export interface DimensionDetail {
  score: number;
  detail: Record<string, unknown>;
}
export interface BranchScorecard {
  branch: string;
  dimensions: Record<string, DimensionDetail>;
  composite_score: number;
}
export interface ArchetypeProfile {
  branch: string;
  composite_score: number;
  channel_mix: Record<string, number>;
  top_categories: Record<string, number>;
  beverage_pct: number;
  recommendation: string;
}
export interface CandidateLocation {
  area: string;
  governorate: string;
  score: number;
  population: number;
  university_nearby: boolean;
  foot_traffic_tier: number;
  rent_tier: number;
  cafe_density: string;
  pros: string[];
  cons: string[];
}
export interface ExpansionResponse {
  verdict: string;
  verdict_detail: string;
  best_archetype: ArchetypeProfile;
  scorecards: BranchScorecard[];
  candidate_locations: CandidateLocation[];
  risks: string[];
  explanation: string;
}

/* ──────────────────────── Growth ────────────────────────── */
export interface GrowthRequest {
  branch: string;
}
export interface HeroItem {
  item: string;
  qty: number;
  revenue: number;
  rank: number;
}
export interface UnderperformingItem {
  item: string;
  your_qty: number;
  best_branch: string;
  best_qty: number;
  gap_pct: number;
}
export interface BundleRecommendation {
  dessert: string;
  beverage: string;
  co_occurrence_count: number;
}
export interface RevenueMomentum {
  months_available: number;
  latest_month: string;
  mom_growth_pct: number;
  trend: string;
}
export interface ChannelDetail {
  channel: string;
  customers: number;
  avg_ticket: number;
}
export interface CustomerMetrics {
  total_customers: number;
  total_sales: number;
  avg_ticket: number;
  channels: ChannelDetail[];
}
export interface DeliveryRepeatRate {
  delivery_customers: number;
  repeat_customers: number;
  repeat_rate_pct: number;
  avg_orders_per_customer: number;
}
export interface StaffingCapacity {
  total_staff_hours: number;
  unique_employees: number;
  bev_per_staff_hour: number;
  insight: string;
}
export interface BranchBeverageProfile {
  branch: string;
  beverage_penetration_pct: number;
  penetration_rank: number;
  coffee_qty: number;
  coffee_revenue: number;
  milkshake_qty: number;
  milkshake_revenue: number;
  frappe_qty: number;
  frappe_revenue: number;
  hero_coffee_items: HeroItem[];
  hero_milkshake_items: HeroItem[];
  underperforming_items: UnderperformingItem[];
  channel_insight: string;
  bundle_recommendations: BundleRecommendation[];
  revenue_momentum: RevenueMomentum;
  customer_metrics: CustomerMetrics;
  delivery_repeat_rate: DeliveryRepeatRate;
  staffing_capacity: StaffingCapacity;
  actions: string[];
}
export interface GrowthResponse {
  branch: string;
  branches: BranchBeverageProfile[];
  explanation: string;
}

/* ──────────────────────── API ───────────────────────────── */
export const api = {
  health: () => client.get<HealthResponse>("/health").then((r) => r.data),
  chat: (data: ChatRequest) =>
    client.post<ChatResponse>("/chat", data).then((r) => r.data),
  combo: (data: ComboRequest) =>
    client.post<ComboResponse>("/combo", data).then((r) => r.data),
  forecast: (data: ForecastRequest) =>
    client.post<ForecastResponse>("/forecast", data).then((r) => r.data),
  staffing: (data: StaffingRequest) =>
    client.post<StaffingResponse>("/staffing", data).then((r) => r.data),
  expansion: (data: ExpansionRequest) =>
    client.post<ExpansionResponse>("/expansion", data).then((r) => r.data),
  growth: (data: GrowthRequest) =>
    client.post<GrowthResponse>("/growth-strategy", data).then((r) => r.data),
};

/* ──────────────────────── Error helper ──────────────────── */
export function isApiError(err: unknown): string {
  if (err instanceof AxiosError) {
    return err.response?.data?.detail || err.message || "API request failed";
  }
  return (err as Error)?.message || "Unknown error";
}

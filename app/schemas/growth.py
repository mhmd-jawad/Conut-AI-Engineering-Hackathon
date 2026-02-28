from pydantic import BaseModel, Field
from typing import Optional


class GrowthRequest(BaseModel):
    branch: str = Field(
        ..., min_length=1,
        description="Branch name or 'all' for cross-branch comparison",
    )


# ── Response models ────────────────────────────────────────────────────────

class HeroItem(BaseModel):
    item: str
    qty: int
    revenue: float
    rank: int = Field(description="Rank within this branch (1 = best)")


class UnderperformingItem(BaseModel):
    item: str
    your_qty: int
    best_branch: str
    best_qty: int
    gap_pct: float = Field(description="How far behind the best branch (%)")


class BundleRecommendation(BaseModel):
    dessert: str
    beverage: str
    co_occurrence_count: int = Field(description="Baskets containing both items")


class RevenueMomentum(BaseModel):
    months_available: int = Field(description="Number of months with data")
    latest_month: str
    mom_growth_pct: float = Field(description="Month-over-month revenue growth %")
    trend: str = Field(description="growing | stable | declining | no data")


class ChannelDetail(BaseModel):
    channel: str
    customers: int
    avg_ticket: float


class CustomerMetrics(BaseModel):
    total_customers: int
    total_sales: float
    avg_ticket: float
    channels: list[ChannelDetail]


class DeliveryRepeatRate(BaseModel):
    delivery_customers: int
    repeat_customers: int
    repeat_rate_pct: float
    avg_orders_per_customer: float


class StaffingCapacity(BaseModel):
    total_staff_hours: float
    unique_employees: int
    bev_per_staff_hour: float = Field(description="Beverage units produced per staff hour")
    insight: str


class BranchBeverageProfile(BaseModel):
    branch: str
    beverage_penetration_pct: float = Field(description="Beverage revenue as % of total branch revenue")
    penetration_rank: int = Field(description="Rank among all branches (1 = highest penetration)")
    coffee_qty: int
    coffee_revenue: float
    milkshake_qty: int
    milkshake_revenue: float
    frappe_qty: int
    frappe_revenue: float
    hero_coffee_items: list[HeroItem]
    hero_milkshake_items: list[HeroItem]
    underperforming_items: list[UnderperformingItem]
    channel_insight: str
    bundle_recommendations: list[BundleRecommendation]
    revenue_momentum: RevenueMomentum
    customer_metrics: CustomerMetrics
    delivery_repeat_rate: DeliveryRepeatRate
    staffing_capacity: StaffingCapacity
    actions: list[str] = Field(description="5-8 data-driven growth recommendations")


class GrowthResponse(BaseModel):
    branch: str
    branches: list[BranchBeverageProfile]
    explanation: str

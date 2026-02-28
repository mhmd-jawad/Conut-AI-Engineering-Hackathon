"""
growth_service.py
-----------------
Coffee & Milkshake Growth Strategy engine.

Analyses beverage performance across branches and generates actionable
recommendations: hero products, underperformers, channel gaps,
dessert-beverage bundles, revenue momentum, staffing capacity, and
per-customer beverage metrics.

Data sources (all 7 processed CSVs):
  - Sales by items and groups.csv          (item-level qty + revenue by branch/division)
  - Summary by division-menu channel.csv   (channel split per division per branch)
  - basket_lines.csv                       (delivery baskets for co-purchase analysis)
  - avg_sales_by_menu_channel.csv          (customer counts + avg ticket per channel)
  - monthly_sales_by_branch.csv            (month-over-month revenue trend)
  - customer_orders_delivery.csv           (delivery repeat-customer patterns)
  - time_attendance_dec2025.csv            (staff hours → capacity for beverage prep)
"""

from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

# Beverage divisions in the item-sales file
COFFEE_DIVISIONS = {"Hot-Coffee Based", "Frappes", "CONUT''S FAVORITE"}
SHAKE_DIVISIONS = {"Shakes"}
ALL_BEV_DIVISIONS = COFFEE_DIVISIONS | SHAKE_DIVISIONS | {"Hot and Cold Drinks", "Bev Add-ons"}

# For growth analysis we focus on revenue-generating items only (price > 0)
# Divisions used for the three KPI buckets
COFFEE_DIV = "Hot-Coffee Based"
FRAPPE_DIV = "Frappes"
SHAKE_DIV = "Shakes"

# Dessert divisions (used for bundle analysis)
DESSERT_KEYWORDS = {"CHIMNEY", "CONUT", "MINI", "BOWL", "BITES", "ICE CREAM", "TIRAMISU"}


# ---------------------------------------------------------------------------
# Data loaders (cached)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_item_sales() -> pd.DataFrame:
    path = DATA_DIR / "Sales by items and groups.csv"
    df = pd.read_csv(path)
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0)
    return df


@functools.lru_cache(maxsize=1)
def _load_channel_summary() -> pd.DataFrame:
    path = DATA_DIR / "Summary by division-menu channel.csv"
    df = pd.read_csv(path)
    for col in ["delivery", "table", "take_away", "total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@functools.lru_cache(maxsize=1)
def _load_basket_lines() -> pd.DataFrame:
    path = DATA_DIR / "basket_lines.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["Is Cancellation"] = df["Is Cancellation"].astype(int)
    df["Is_Modifier"] = df["Is_Modifier"].astype(int)
    return df


@functools.lru_cache(maxsize=1)
def _load_monthly_sales() -> pd.DataFrame:
    path = DATA_DIR / "monthly_sales_by_branch.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
    # Create a sortable month index
    month_order = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12,
    }
    df["month_num"] = df["month"].map(month_order)
    df = df.sort_values(["branch", "year", "month_num"])
    return df


@functools.lru_cache(maxsize=1)
def _load_avg_sales_channel() -> pd.DataFrame:
    path = DATA_DIR / "avg_sales_by_menu_channel.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    for col in ["num_customers", "sales", "avg_per_customer"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@functools.lru_cache(maxsize=1)
def _load_customer_orders() -> pd.DataFrame:
    path = DATA_DIR / "customer_orders_delivery.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["num_orders"] = pd.to_numeric(df["num_orders"], errors="coerce").fillna(0)
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
    return df


@functools.lru_cache(maxsize=1)
def _load_attendance() -> pd.DataFrame:
    path = DATA_DIR / "time_attendance_dec2025.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["Duration Hours"] = pd.to_numeric(df["Duration Hours"], errors="coerce").fillna(0)
    return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_beverage_item(desc: str) -> bool:
    """Heuristic: item name contains beverage keywords."""
    d = desc.upper()
    bev_kw = {
        "COFFEE", "ESPRESSO", "LATTE", "CAPPUCCINO", "AMERICANO", "MOCHA",
        "FRAPPE", "MILKSHAKE", "SHAKE", "CHOCOLATE COMBO", "MATCHA",
        "MACCHIATO", "MACHIATO", "FLAT WHITE", "AFFOGATO", "WHITE MOCHA",
    }
    return any(kw in d for kw in bev_kw)


def _is_dessert_item(desc: str) -> bool:
    d = desc.upper()
    return any(kw in d for kw in DESSERT_KEYWORDS)


def _top_items(df: pd.DataFrame, division: str, branch: str, n: int = 3) -> list[dict]:
    """Return top-n items by qty in a division for a branch (revenue > 0 only)."""
    sub = df[(df["division"] == division) & (df["branch"] == branch) & (df["qty"] > 0) & (df["total_amount"] > 0)]
    sub = sub.sort_values("qty", ascending=False).head(n)
    return [
        {"item": r["description"], "qty": int(r["qty"]), "revenue": round(r["total_amount"], 2), "rank": i + 1}
        for i, (_, r) in enumerate(sub.iterrows())
    ]


def _division_totals(df: pd.DataFrame, division: str, branch: str) -> tuple[int, float]:
    """Return (total_qty, total_revenue) for a division at a branch."""
    sub = df[(df["division"] == division) & (df["branch"] == branch) & (df["qty"] > 0)]
    return int(sub["qty"].sum()), round(float(sub["total_amount"].sum()), 2)


def _find_underperformers(df: pd.DataFrame, divisions: list[str], branch: str, all_branches: list[str]) -> list[dict]:
    """Items that sell well at other branches but poorly at this branch."""
    results = []
    for div in divisions:
        # Get qty per item per branch for this division
        sub = df[(df["division"] == div) & (df["qty"] > 0)]
        pivot = sub.groupby(["description", "branch"])["qty"].sum().reset_index()

        # For each item, find the best branch
        for item in pivot["description"].unique():
            item_data = pivot[pivot["description"] == item]
            best_row = item_data.loc[item_data["qty"].idxmax()]
            best_branch = best_row["branch"]
            best_qty = int(best_row["qty"])

            if best_branch == branch:
                continue  # This branch IS the best — skip

            # What does this branch sell?
            this_qty_row = item_data[item_data["branch"] == branch]
            this_qty = int(this_qty_row["qty"].iloc[0]) if len(this_qty_row) > 0 else 0

            if best_qty <= 3:
                continue  # Not enough volume to matter

            gap_pct = round((1 - this_qty / best_qty) * 100, 1) if best_qty > 0 else 100.0
            if gap_pct >= 40:  # At least 40% behind
                results.append({
                    "item": item,
                    "your_qty": this_qty,
                    "best_branch": best_branch,
                    "best_qty": best_qty,
                    "gap_pct": gap_pct,
                })

    # Sort by gap severity, limit to top 5
    results.sort(key=lambda r: r["gap_pct"], reverse=True)
    return results[:5]


def _channel_insight(channel_df: pd.DataFrame, branch: str) -> str:
    """Generate channel insight for beverage sales at a branch."""
    bev_divs = [COFFEE_DIV, FRAPPE_DIV, SHAKE_DIV]
    sub = channel_df[(channel_df["section"] == branch) & (channel_df["item"].isin(bev_divs))]

    if sub.empty:
        return f"No channel data available for beverages at {branch}."

    delivery = sub["delivery"].sum()
    table = sub["table"].sum()
    takeaway = sub["take_away"].sum()
    total = delivery + table + takeaway

    if total == 0:
        return f"No beverage revenue recorded across any channel at {branch}."

    parts = []
    if delivery > 0:
        parts.append(f"Delivery: {delivery / total * 100:.0f}%")
    if table > 0:
        parts.append(f"Table: {table / total * 100:.0f}%")
    if takeaway > 0:
        parts.append(f"Take-away: {takeaway / total * 100:.0f}%")

    channel_mix = ", ".join(parts)
    insight = f"Channel mix — {channel_mix}."

    if delivery == 0 and total > 0:
        insight += " No beverage delivery sales — consider enabling delivery for drinks."
    if takeaway == 0 and total > 0:
        insight += " No take-away beverage sales — consider promoting grab-and-go beverages."

    return insight


def _beverage_bundles(basket_df: pd.DataFrame, branch: str, top_n: int = 5) -> list[dict]:
    """Find dessert-beverage co-purchases from basket data."""
    if basket_df.empty:
        return []

    df = basket_df[basket_df["Is Cancellation"] == 0].copy()
    if branch.lower() != "all":
        df = df[df["Branch"].str.strip().str.lower() == branch.lower()]

    if df.empty:
        return []

    # Build baskets
    baskets: dict[str, set[str]] = {}
    for bid, group in df.groupby("basket_id"):
        items = set(group["Item Description"].unique())
        if len(items) >= 2:
            baskets[bid] = items

    # Count dessert-beverage co-occurrences
    from collections import Counter
    pair_counts: Counter[tuple[str, str]] = Counter()

    for items in baskets.values():
        bev_items = {i for i in items if _is_beverage_item(i)}
        des_items = {i for i in items if _is_dessert_item(i)}
        for d in des_items:
            for b in bev_items:
                pair_counts[(d, b)] += 1

    # Top pairs
    top_pairs = pair_counts.most_common(top_n)
    return [
        {"dessert": d, "beverage": b, "co_occurrence_count": cnt}
        for (d, b), cnt in top_pairs if cnt >= 1
    ]


def _revenue_momentum(monthly_df: pd.DataFrame, branch: str) -> dict:
    """Compute month-over-month revenue trend for a branch."""
    if monthly_df.empty:
        return {"months_available": 0, "latest_month": "N/A", "mom_growth_pct": 0.0, "trend": "no data"}

    sub = monthly_df[monthly_df["branch"] == branch].sort_values(["year", "month_num"])
    if len(sub) < 2:
        return {"months_available": len(sub), "latest_month": "N/A", "mom_growth_pct": 0.0, "trend": "insufficient data"}

    totals = sub["total"].tolist()
    months = sub["month"].tolist()
    latest = totals[-1]
    previous = totals[-2]

    mom_pct = round((latest - previous) / previous * 100, 1) if previous > 0 else 0.0

    # Overall trend: compare first half avg vs second half avg
    mid = len(totals) // 2
    first_avg = sum(totals[:mid]) / mid if mid > 0 else 0
    second_avg = sum(totals[mid:]) / (len(totals) - mid) if (len(totals) - mid) > 0 else 0

    if second_avg > first_avg * 1.1:
        trend = "growing"
    elif second_avg < first_avg * 0.9:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "months_available": len(sub),
        "latest_month": months[-1],
        "mom_growth_pct": mom_pct,
        "trend": trend,
    }


def _customer_metrics(avg_channel_df: pd.DataFrame, branch: str) -> dict:
    """Compute customer traffic and avg ticket insights for a branch."""
    if avg_channel_df.empty:
        return {"total_customers": 0, "total_sales": 0.0, "avg_ticket": 0.0, "channels": []}

    sub = avg_channel_df[avg_channel_df["branch"] == branch]
    if sub.empty:
        return {"total_customers": 0, "total_sales": 0.0, "avg_ticket": 0.0, "channels": []}

    total_cust = int(sub["num_customers"].sum())
    total_sales = float(sub["sales"].sum())
    avg_ticket = round(total_sales / total_cust, 2) if total_cust > 0 else 0.0

    channels = []
    for _, row in sub.iterrows():
        channels.append({
            "channel": row["channel"],
            "customers": int(row["num_customers"]),
            "avg_ticket": round(float(row["avg_per_customer"]), 2),
        })

    return {
        "total_customers": total_cust,
        "total_sales": round(total_sales, 2),
        "avg_ticket": avg_ticket,
        "channels": channels,
    }


def _delivery_repeat_rate(cust_orders_df: pd.DataFrame, branch: str) -> dict:
    """Compute delivery customer repeat-order rate."""
    if cust_orders_df.empty:
        return {"delivery_customers": 0, "repeat_customers": 0, "repeat_rate_pct": 0.0, "avg_orders_per_customer": 0.0}

    sub = cust_orders_df[cust_orders_df["branch"] == branch]
    if sub.empty:
        return {"delivery_customers": 0, "repeat_customers": 0, "repeat_rate_pct": 0.0, "avg_orders_per_customer": 0.0}

    total = len(sub)
    repeat = len(sub[sub["num_orders"] > 1])
    avg_orders = round(float(sub["num_orders"].mean()), 2)

    return {
        "delivery_customers": total,
        "repeat_customers": repeat,
        "repeat_rate_pct": round(repeat / total * 100, 1) if total > 0 else 0.0,
        "avg_orders_per_customer": avg_orders,
    }


def _staffing_insight(attendance_df: pd.DataFrame, branch: str, bev_qty: int) -> dict:
    """Compute total staff hours and beverage units per staff hour."""
    if attendance_df.empty:
        return {"total_staff_hours": 0.0, "unique_employees": 0, "bev_per_staff_hour": 0.0, "insight": "No attendance data."}

    sub = attendance_df[attendance_df["Branch"] == branch]
    if sub.empty:
        return {"total_staff_hours": 0.0, "unique_employees": 0, "bev_per_staff_hour": 0.0, "insight": f"No attendance data for {branch}."}

    total_hours = round(float(sub["Duration Hours"].sum()), 1)
    unique_emp = int(sub["Emp ID"].nunique())
    bev_per_hour = round(bev_qty / total_hours, 2) if total_hours > 0 else 0.0

    insight = f"{unique_emp} employees, {total_hours:.0f} total hours (Dec 2025). "
    if bev_per_hour < 1:
        insight += "Low beverage throughput per staff hour — consider barista training."
    else:
        insight += f"Producing {bev_per_hour} beverage units per staff hour."

    return {
        "total_staff_hours": total_hours,
        "unique_employees": unique_emp,
        "bev_per_staff_hour": bev_per_hour,
        "insight": insight,
    }


def _generate_actions(
    branch: str,
    coffee_qty: int,
    shake_qty: int,
    frappe_qty: int,
    penetration_pct: float,
    heroes_coffee: list[dict],
    heroes_shake: list[dict],
    underperformers: list[dict],
    channel_insight_text: str,
    bundles: list[dict],
    all_branch_stats: dict[str, dict],
    momentum: dict,
    cust_metrics: dict,
    staffing: dict,
    delivery_repeat: dict,
) -> list[str]:
    """Generate 5-8 plain-English actionable recommendations using ALL data signals."""
    actions = []

    # Find the benchmark branch (highest total bev qty)
    benchmark = max(all_branch_stats, key=lambda b: all_branch_stats[b]["total_bev_qty"])
    bench_qty = all_branch_stats[benchmark]["total_bev_qty"]
    my_qty = coffee_qty + shake_qty + frappe_qty

    # 1. Overall position
    if my_qty < bench_qty * 0.5:
        actions.append(
            f"URGENT: Beverage volume is {my_qty} units — {((1 - my_qty / bench_qty) * 100):.0f}% behind "
            f"{benchmark} ({bench_qty} units). Prioritise beverage promotion and staff training."
        )
    elif my_qty < bench_qty * 0.8:
        actions.append(
            f"Beverage volume ({my_qty}) trails {benchmark} ({bench_qty}) by "
            f"{((1 - my_qty / bench_qty) * 100):.0f}%. Target coffee upselling during peak hours."
        )

    # 2. Momentum signal
    if momentum["trend"] == "declining":
        actions.append(
            f"WARNING: Revenue is declining (MoM: {momentum['mom_growth_pct']:+.1f}% in {momentum['latest_month']}). "
            f"Investigate root cause — pricing, footfall, or competition."
        )
    elif momentum["trend"] == "growing" and momentum["mom_growth_pct"] > 20:
        actions.append(
            f"Strong momentum: {momentum['mom_growth_pct']:+.1f}% MoM growth in {momentum['latest_month']}. "
            f"Capitalise by expanding beverage range while traffic is up."
        )

    # 3. Per-customer beverage revenue
    if cust_metrics["total_customers"] > 0:
        bev_rev = all_branch_stats.get(branch, {}).get("bev_rev", 0)
        bev_per_cust = round(bev_rev / cust_metrics["total_customers"], 2) if cust_metrics["total_customers"] else 0
        # Compare to best branch
        best_bpc = 0
        best_bpc_branch = branch
        for b, s in all_branch_stats.items():
            b_cust = s.get("total_customers", 0)
            if b_cust > 0:
                b_bpc = s["bev_rev"] / b_cust
                if b_bpc > best_bpc:
                    best_bpc = b_bpc
                    best_bpc_branch = b
        if best_bpc > 0 and bev_per_cust < best_bpc * 0.6:
            actions.append(
                f"Low beverage spend per customer ({bev_per_cust:,.0f} vs {best_bpc:,.0f} at {best_bpc_branch}). "
                f"Train staff on upselling drinks with every dessert order."
            )

    # 4. Staffing capacity
    if staffing["bev_per_staff_hour"] > 0 and staffing["bev_per_staff_hour"] < 0.5:
        actions.append(
            f"Low beverage throughput ({staffing['bev_per_staff_hour']} units/staff-hour). "
            f"Consider dedicated barista shifts or workflow optimisation."
        )

    # 5. Delivery repeat rate
    if delivery_repeat["delivery_customers"] > 5 and delivery_repeat["repeat_rate_pct"] < 15:
        actions.append(
            f"Delivery repeat rate is only {delivery_repeat['repeat_rate_pct']:.0f}% "
            f"({delivery_repeat['repeat_customers']}/{delivery_repeat['delivery_customers']} customers). "
            f"Launch a loyalty or bundled-delivery beverage deal."
        )
    elif delivery_repeat["delivery_customers"] == 0:
        actions.append("No delivery customers — consider launching a delivery beverage menu.")

    # 6. Hero products to push
    if heroes_coffee:
        top_c = heroes_coffee[0]["item"]
        actions.append(f"Push hero coffee: {top_c} (your #1 seller with {heroes_coffee[0]['qty']} units).")
    if heroes_shake:
        top_s = heroes_shake[0]["item"]
        actions.append(f"Push hero milkshake: {top_s} (your #1 shake with {heroes_shake[0]['qty']} units).")

    # 7. Underperformer action
    if underperformers:
        worst = underperformers[0]
        actions.append(
            f"Growth opportunity: {worst['item']} sells {worst['best_qty']} units at {worst['best_branch']} "
            f"but only {worst['your_qty']} here ({worst['gap_pct']:.0f}% gap). Investigate visibility and staffing."
        )

    # 8. Channel action
    if "No beverage delivery" in channel_insight_text:
        actions.append("Enable beverage delivery — other branches show delivery demand for drinks.")
    if "No take-away" in channel_insight_text:
        actions.append("Add grab-and-go beverage promotion for take-away customers.")

    # 9. Bundle action
    if bundles:
        top_bundle = bundles[0]
        actions.append(
            f"Bundle opportunity: {top_bundle['dessert']} + {top_bundle['beverage']} "
            f"(co-purchased {top_bundle['co_occurrence_count']}x). Create a combo deal."
        )

    return actions[:8]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def growth_strategy(branch: str) -> dict:
    """Return beverage growth strategy for *branch* (or 'all')."""

    item_df = _load_item_sales()
    channel_df = _load_channel_summary()
    basket_df = _load_basket_lines()
    monthly_df = _load_monthly_sales()
    avg_ch_df = _load_avg_sales_channel()
    cust_orders_df = _load_customer_orders()
    attendance_df = _load_attendance()

    all_branches = sorted(item_df["branch"].unique())
    branch_label = branch.strip()

    # Determine which branches to analyse
    if branch_label.lower() == "all":
        target_branches = all_branches
    else:
        # Case-insensitive match
        matched = [b for b in all_branches if b.lower() == branch_label.lower()]
        if not matched:
            return {
                "branch": branch_label,
                "branches": [],
                "explanation": f"Branch '{branch_label}' not found. Available: {', '.join(all_branches)}",
            }
        target_branches = matched

    # Pre-compute cross-branch stats for benchmarking
    all_branch_stats: dict[str, dict] = {}
    for b in all_branches:
        cq, cr = _division_totals(item_df, COFFEE_DIV, b)
        fq, fr = _division_totals(item_df, FRAPPE_DIV, b)
        sq, sr = _division_totals(item_df, SHAKE_DIV, b)
        total_rev = float(item_df[item_df["branch"] == b]["total_amount"].sum())
        bev_rev = cr + fr + sr
        cm = _customer_metrics(avg_ch_df, b)
        all_branch_stats[b] = {
            "coffee_qty": cq, "coffee_rev": cr,
            "frappe_qty": fq, "frappe_rev": fr,
            "shake_qty": sq, "shake_rev": sr,
            "total_bev_qty": cq + fq + sq,
            "bev_rev": bev_rev,
            "total_rev": total_rev,
            "penetration_pct": round(bev_rev / total_rev * 100, 2) if total_rev > 0 else 0.0,
            "total_customers": cm["total_customers"],
        }

    # Rank branches by penetration
    ranked = sorted(all_branch_stats.items(), key=lambda x: x[1]["penetration_pct"], reverse=True)
    rank_map = {b: i + 1 for i, (b, _) in enumerate(ranked)}

    # Build profiles
    profiles = []
    for b in target_branches:
        stats = all_branch_stats[b]

        heroes_coffee = _top_items(item_df, COFFEE_DIV, b, n=3)
        heroes_shake = _top_items(item_df, SHAKE_DIV, b, n=3)

        underperformers = _find_underperformers(
            item_df, [COFFEE_DIV, FRAPPE_DIV, SHAKE_DIV], b, all_branches
        )

        ch_insight = _channel_insight(channel_df, b)
        bundles = _beverage_bundles(basket_df, b, top_n=5)
        momentum = _revenue_momentum(monthly_df, b)
        cust_met = _customer_metrics(avg_ch_df, b)
        delivery_rep = _delivery_repeat_rate(cust_orders_df, b)
        staffing = _staffing_insight(attendance_df, b, stats["total_bev_qty"])

        actions = _generate_actions(
            branch=b,
            coffee_qty=stats["coffee_qty"],
            shake_qty=stats["shake_qty"],
            frappe_qty=stats["frappe_qty"],
            penetration_pct=stats["penetration_pct"],
            heroes_coffee=heroes_coffee,
            heroes_shake=heroes_shake,
            underperformers=underperformers,
            channel_insight_text=ch_insight,
            bundles=bundles,
            all_branch_stats=all_branch_stats,
            momentum=momentum,
            cust_metrics=cust_met,
            staffing=staffing,
            delivery_repeat=delivery_rep,
        )

        profiles.append({
            "branch": b,
            "beverage_penetration_pct": stats["penetration_pct"],
            "penetration_rank": rank_map[b],
            "coffee_qty": stats["coffee_qty"],
            "coffee_revenue": stats["coffee_rev"],
            "milkshake_qty": stats["shake_qty"],
            "milkshake_revenue": stats["shake_rev"],
            "frappe_qty": stats["frappe_qty"],
            "frappe_revenue": stats["frappe_rev"],
            "hero_coffee_items": heroes_coffee,
            "hero_milkshake_items": heroes_shake,
            "underperforming_items": underperformers,
            "channel_insight": ch_insight,
            "bundle_recommendations": bundles,
            "revenue_momentum": momentum,
            "customer_metrics": cust_met,
            "delivery_repeat_rate": delivery_rep,
            "staffing_capacity": staffing,
            "actions": actions,
        })

    explanation = (
        f"Analysed beverage performance across {len(all_branches)} branches using ALL 7 processed data files. "
        f"Beverage divisions: Hot-Coffee Based, Frappes, Shakes. "
        f"Penetration = beverage revenue / total branch revenue. "
        f"Underperformers = items ≥40% behind the best branch by qty. "
        f"Bundles from delivery basket co-purchase data (Jan 2026). "
        f"Revenue momentum from monthly_sales_by_branch (Aug-Dec 2025). "
        f"Customer metrics from avg_sales_by_menu_channel (traffic + avg ticket). "
        f"Delivery repeat rate from customer_orders_delivery (539 customers). "
        f"Staffing capacity from time_attendance_dec2025 (273 shift records)."
    )

    return {
        "branch": branch_label,
        "branches": profiles,
        "explanation": explanation,
    }

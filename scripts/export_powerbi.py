"""
export_powerbi.py
=================
Maven Fuzzy Factory – Power BI Data Export
Author : Binh Pham | GitHub: binhpham-2002

Reads cleaned CSVs → builds aggregated, Power-BI-ready tables →
writes to powerbi/dashboard_data/
"""

import os
import pandas as pd

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR    = os.path.join(BASE_DIR, "data", "processed")
EXPORT_DIR  = os.path.join(BASE_DIR, "powerbi", "dashboard_data")
os.makedirs(EXPORT_DIR, exist_ok=True)

def load(filename: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(PROC_DIR, filename), parse_dates=["created_at"])

def save(df: pd.DataFrame, filename: str) -> None:
    path = os.path.join(EXPORT_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  ✔  {filename}  ({df.shape[0]:,} rows)")


# ── Load cleaned tables ──────────────────────────────────────────────────────
print("\n📂  Loading cleaned data…")
orders    = load("cleaned_orders.csv")
items     = load("cleaned_order_items.csv")
refunds   = load("cleaned_order_item_refunds.csv")
products  = load("cleaned_products.csv")
sessions  = load("cleaned_website_sessions.csv")
pageviews = load("cleaned_website_pageviews.csv")
master    = load("master_orders.csv")


print("\n📊  Building Power BI tables…\n")

# ── 1. Monthly Revenue KPIs ──────────────────────────────────────────────────
monthly_revenue = (
    master.groupby("year_month").agg(
        orders        = ("order_id",    "nunique"),
        revenue       = ("price_usd",   "sum"),
        cogs          = ("cogs_usd",    "sum"),
        gross_profit  = ("gross_profit","sum"),
        avg_order_val = ("price_usd",   "mean"),
    ).round(2).reset_index()
)
# Rolling MoM growth
monthly_revenue["revenue_mom_pct"] = (
    monthly_revenue["revenue"].pct_change() * 100
).round(2)
save(monthly_revenue, "pbi_monthly_revenue.csv")


# ── 2. Traffic Channel Performance ──────────────────────────────────────────
channel_perf = (
    master.groupby(["utm_source", "utm_campaign"]).agg(
        orders   = ("order_id",  "nunique"),
        revenue  = ("price_usd", "sum"),
        sessions = ("website_session_id", "nunique"),
    ).round(2).reset_index()
)
# Merge total sessions (including non-converting)
sess_agg = (
    sessions.groupby(["utm_source", "utm_campaign"])
    .agg(total_sessions=("website_session_id", "nunique"))
    .reset_index()
)
channel_perf = channel_perf.merge(sess_agg, on=["utm_source","utm_campaign"], how="left")
channel_perf["cvr_pct"] = (
    channel_perf["orders"] / channel_perf["total_sessions"] * 100
).round(2)
save(channel_perf, "pbi_channel_performance.csv")


# ── 3. Product Performance ───────────────────────────────────────────────────
product_perf = (
    items.merge(products[["product_id","product_name"]], on="product_id")
    .groupby(["product_id","product_name","year_month"]).agg(
        units_sold   = ("order_item_id", "count"),
        revenue      = ("price_usd",     "sum"),
        gross_profit = ("gross_profit",  "sum"),
    ).round(2).reset_index()
)
save(product_perf, "pbi_product_performance.csv")


# ── 4. Refund Summary by Product ─────────────────────────────────────────────
refund_by_product = (
    items.merge(refunds, on="order_item_id", how="left", suffixes=("","_r"))
    .merge(products[["product_id","product_name"]], on="product_id")
    .groupby("product_name").agg(
        units_sold        = ("order_item_id", "count"),
        units_refunded    = ("order_item_refund_id", "count"),
        total_refund_usd  = ("refund_amount_usd", "sum"),
    ).reset_index()
)
refund_by_product["refund_rate_pct"] = (
    refund_by_product["units_refunded"] / refund_by_product["units_sold"] * 100
).round(2)
save(refund_by_product, "pbi_refund_by_product.csv")


# ── 5. Device-type Sessions ──────────────────────────────────────────────────
device_sessions = (
    sessions.groupby(["year_month", "device_type"]).agg(
        sessions = ("website_session_id", "nunique"),
    ).reset_index()
)
save(device_sessions, "pbi_device_sessions.csv")


# ── 6. Top Pages ─────────────────────────────────────────────────────────────
top_pages = (
    pageviews.groupby("pageview_url").agg(
        pageviews        = ("website_pageview_id", "count"),
        unique_sessions  = ("website_session_id",  "nunique"),
    ).reset_index()
    .sort_values("pageviews", ascending=False)
)
save(top_pages, "pbi_top_pages.csv")


# ── 7. Customer-level CLV ────────────────────────────────────────────────────
clv = (
    master.groupby("user_id").agg(
        total_orders  = ("order_id",    "nunique"),
        lifetime_rev  = ("price_usd",   "sum"),
        avg_order_val = ("price_usd",   "mean"),
        first_order   = ("created_at",  "min"),
        last_order    = ("created_at",  "max"),
        channel       = ("utm_source",  "first"),
        device        = ("device_type", "first"),
    ).round(2).reset_index()
)
clv["days_active"] = (clv["last_order"] - clv["first_order"]).dt.days
save(clv, "pbi_customer_clv.csv")


print("\n✅  Power BI export complete → powerbi/dashboard_data/")

"""
data_cleaning.py
================
Maven Fuzzy Factory – E-Commerce Data Cleaning Pipeline
Author : Binh Pham | GitHub: binhpham-2002

Reads raw CSVs → validates → cleans → writes processed CSVs to data/processed/
"""

import os
import pandas as pd
import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR  = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────────────
def load(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    df   = pd.read_csv(path)
    print(f"\n{'='*55}")
    print(f"  Loaded: {filename}  ({df.shape[0]:,} rows × {df.shape[1]} cols)")
    print(f"{'='*55}")
    return df


def summarise(df: pd.DataFrame, name: str) -> None:
    print(f"\n── {name} ── Missing values ──")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("  ✔  No missing values")
    else:
        print(missing.to_string())
    print(f"  Dtypes : {dict(df.dtypes)}")


def save(df: pd.DataFrame, filename: str) -> None:
    path = os.path.join(PROC_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  ✔  Saved → {filename}  ({df.shape[0]:,} rows)")


# ── 1. Orders ────────────────────────────────────────────────────────────────
def clean_orders() -> pd.DataFrame:
    df = load("orders.csv")
    summarise(df, "orders")

    df["created_at"] = pd.to_datetime(df["created_at"])

    # Derived columns
    df["year"]         = df["created_at"].dt.year
    df["month"]        = df["created_at"].dt.month
    df["year_month"]   = df["created_at"].dt.to_period("M").astype(str)
    df["quarter"]      = df["created_at"].dt.to_period("Q").astype(str)
    df["gross_profit"] = (df["price_usd"] - df["cogs_usd"]).round(2)
    df["margin_pct"]   = (df["gross_profit"] / df["price_usd"] * 100).round(2)

    # Sanity checks
    assert (df["price_usd"] >= 0).all(), "Negative price detected"
    assert (df["cogs_usd"]  >= 0).all(), "Negative COGS detected"
    assert df["order_id"].is_unique,     "Duplicate order_id detected"

    save(df, "cleaned_orders.csv")
    return df


# ── 2. Order Items ───────────────────────────────────────────────────────────
def clean_order_items() -> pd.DataFrame:
    df = load("order_items.csv")
    summarise(df, "order_items")

    df["created_at"]   = pd.to_datetime(df["created_at"])
    df["year_month"]   = df["created_at"].dt.to_period("M").astype(str)
    df["gross_profit"] = (df["price_usd"] - df["cogs_usd"]).round(2)
    df["margin_pct"]   = (df["gross_profit"] / df["price_usd"] * 100).round(2)

    assert df["order_item_id"].is_unique, "Duplicate order_item_id detected"

    save(df, "cleaned_order_items.csv")
    return df


# ── 3. Order Item Refunds ────────────────────────────────────────────────────
def clean_refunds() -> pd.DataFrame:
    df = load("order_item_refunds.csv")
    summarise(df, "order_item_refunds")

    df["created_at"] = pd.to_datetime(df["created_at"])
    df["year_month"] = df["created_at"].dt.to_period("M").astype(str)

    assert df["order_item_refund_id"].is_unique, "Duplicate refund_id detected"

    save(df, "cleaned_order_item_refunds.csv")
    return df


# ── 4. Products ──────────────────────────────────────────────────────────────
def clean_products() -> pd.DataFrame:
    df = load("products.csv")
    summarise(df, "products")

    df["created_at"]    = pd.to_datetime(df["created_at"])
    df["product_name"]  = df["product_name"].str.strip()

    assert df["product_id"].is_unique, "Duplicate product_id detected"

    save(df, "cleaned_products.csv")
    return df


# ── 5. Website Sessions ──────────────────────────────────────────────────────
def clean_sessions() -> pd.DataFrame:
    df = load("website_sessions.csv")
    summarise(df, "website_sessions")

    df["created_at"] = pd.to_datetime(df["created_at"])
    df["year_month"] = df["created_at"].dt.to_period("M").astype(str)
    df["hour"]       = df["created_at"].dt.hour

    # Fill nulls in UTM columns with 'direct' / 'organic'
    df["utm_source"]   = df["utm_source"].fillna("direct")
    df["utm_campaign"] = df["utm_campaign"].fillna("none")
    df["utm_content"]  = df["utm_content"].fillna("none")

    # Normalise device_type to lowercase
    df["device_type"] = df["device_type"].str.lower().str.strip()

    assert df["website_session_id"].is_unique, "Duplicate session_id detected"

    save(df, "cleaned_website_sessions.csv")
    return df


# ── 6. Website Pageviews ─────────────────────────────────────────────────────
def clean_pageviews() -> pd.DataFrame:
    df = load("website_pageviews.csv")
    summarise(df, "website_pageviews")

    df["created_at"]   = pd.to_datetime(df["created_at"])
    df["year_month"]   = df["created_at"].dt.to_period("M").astype(str)
    df["pageview_url"] = df["pageview_url"].str.strip().str.lower()

    assert df["website_pageview_id"].is_unique, "Duplicate pageview_id detected"

    save(df, "cleaned_website_pageviews.csv")
    return df


# ── 7. Master Dataset (orders enriched) ─────────────────────────────────────
def build_master(orders, sessions, products) -> pd.DataFrame:
    master = orders.merge(
        sessions[["website_session_id", "utm_source", "utm_campaign",
                  "utm_content", "device_type", "is_repeat_session"]],
        on="website_session_id", how="left"
    ).merge(
        products[["product_id", "product_name"]],
        left_on="primary_product_id", right_on="product_id", how="left"
    )
    save(master, "master_orders.csv")
    print(f"\n  Master dataset shape: {master.shape}")
    return master


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀  Starting Maven Fuzzy Factory Data Cleaning Pipeline…\n")

    orders   = clean_orders()
    items    = clean_order_items()
    refunds  = clean_refunds()
    products = clean_products()
    sessions = clean_sessions()
    pageviews = clean_pageviews()
    master   = build_master(orders, sessions, products)

    print("\n✅  All tables cleaned and saved to data/processed/\n")
    print("Files created:")
    for f in os.listdir(PROC_DIR):
        size = os.path.getsize(os.path.join(PROC_DIR, f)) // 1024
        print(f"  {f}  ({size} KB)")

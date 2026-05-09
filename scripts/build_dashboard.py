"""
build_dashboard.py
==================
Maven Fuzzy Factory – Interactive HTML Dashboard (Plotly)
Author : Binh Pham | GitHub: binhpham-2002

Generates:
  powerbi/ecommerce_dashboard.html  — self-contained interactive dashboard
  notebooks/screenshots/            — PNG charts for README
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC   = os.path.join(BASE, "data", "processed")
EXPORT = os.path.join(BASE, "powerbi", "dashboard_data")
OUT    = os.path.join(BASE, "powerbi")
SS_DIR = os.path.join(BASE, "notebooks", "screenshots")
os.makedirs(SS_DIR, exist_ok=True)

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    "blue":   "#2563EB", "green":  "#16A34A", "amber":  "#D97706",
    "red":    "#DC2626", "purple": "#7C3AED", "teal":   "#0D9488",
    "grey":   "#6B7280", "light":  "#F1F5F9", "white":  "#FFFFFF",
}
PRODUCT_COLORS = ["#2563EB", "#16A34A", "#D97706", "#DC2626"]
TEMPLATE       = "plotly_white"

# ── Load data ─────────────────────────────────────────────────────────────────
print("📂  Loading cleaned data…")
orders   = pd.read_csv(f"{PROC}/cleaned_orders.csv",   parse_dates=["created_at"])
items    = pd.read_csv(f"{PROC}/cleaned_order_items.csv", parse_dates=["created_at"])
refunds  = pd.read_csv(f"{PROC}/cleaned_order_item_refunds.csv", parse_dates=["created_at"])
products = pd.read_csv(f"{PROC}/cleaned_products.csv")
sessions = pd.read_csv(f"{PROC}/cleaned_website_sessions.csv", parse_dates=["created_at"])
master   = pd.read_csv(f"{PROC}/master_orders.csv",    parse_dates=["created_at"])

# Pre-aggregate
monthly = orders.groupby("year_month").agg(
    revenue=("price_usd","sum"), gross_profit=("gross_profit","sum"),
    orders=("order_id","nunique"), avg_order_val=("price_usd","mean")
).round(2).reset_index()
monthly["mom_pct"] = monthly["revenue"].pct_change().mul(100).round(1)

sess_ch = sessions.groupby(["utm_source","utm_campaign"])["website_session_id"].nunique().reset_index(name="total_sessions")
ord_ch  = master.groupby(["utm_source","utm_campaign"])["order_id"].nunique().reset_index(name="orders")
channel = sess_ch.merge(ord_ch, on=["utm_source","utm_campaign"], how="left").fillna(0)
channel["cvr_pct"]  = (channel["orders"] / channel["total_sessions"] * 100).round(2)
channel["rev"]      = master.groupby(["utm_source","utm_campaign"])["price_usd"].sum().reset_index(name="rev")["rev"].values[:len(channel)]
channel["label"]    = channel["utm_source"].str.title() + " / " + channel["utm_campaign"].str.title()

prod_items = items.merge(products[["product_id","product_name"]], on="product_id")
prod_agg   = prod_items.groupby("product_name").agg(
    revenue=("price_usd","sum"), units=("order_item_id","count"), gp=("gross_profit","sum")
).round(2).reset_index()

ref_merged = items.merge(refunds[["order_item_id","refund_amount_usd"]], on="order_item_id", how="left")
ref_merged = ref_merged.merge(products[["product_id","product_name"]], on="product_id")
ref_agg    = ref_merged.groupby("product_name").agg(
    sold=("order_item_id","count"), refunds=("refund_amount_usd","count"), refund_usd=("refund_amount_usd","sum")
).reset_index()
ref_agg["refund_rate"] = (ref_agg["refunds"] / ref_agg["sold"] * 100).round(2)

clv = master.groupby("user_id").agg(
    lifetime_rev=("price_usd","sum"), orders=("order_id","nunique")
).reset_index()

device = sessions.groupby(["year_month","device_type"])["website_session_id"].nunique().reset_index(name="sessions")

# ── KPI cards helper ──────────────────────────────────────────────────────────
def kpi_indicator(value, title, prefix="", suffix="", delta=None):
    fig = go.Figure(go.Indicator(
        mode="number+delta" if delta else "number",
        value=value,
        number={"prefix": prefix, "suffix": suffix,
                "font": {"size": 40, "color": C["blue"], "family": "Inter, sans-serif"}},
        delta={"reference": delta, "relative": True, "valueformat": ".1%"} if delta else None,
        title={"text": f"<b>{title}</b>", "font": {"size": 14, "color": C["grey"]}},
    ))
    fig.update_layout(template=TEMPLATE, margin=dict(l=20,r=20,t=50,b=10), height=130)
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
print("🎨  Building dashboard…")

figs = {}   # store individual figures for screenshots too

# 1. Monthly Revenue + Orders (dual axis)
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Bar(x=monthly["year_month"], y=monthly["revenue"],
    name="Revenue", marker_color=C["blue"], opacity=0.85), secondary_y=False)
fig1.add_trace(go.Bar(x=monthly["year_month"], y=monthly["gross_profit"],
    name="Gross Profit", marker_color=C["green"], opacity=0.85), secondary_y=False)
fig1.add_trace(go.Scatter(x=monthly["year_month"], y=monthly["orders"],
    name="Orders", line=dict(color=C["red"], width=2.5), mode="lines+markers",
    marker=dict(size=5)), secondary_y=True)
fig1.update_layout(template=TEMPLATE, title="📈 Monthly Revenue, Gross Profit & Order Volume",
    barmode="group", legend=dict(orientation="h", y=1.12),
    xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
    yaxis=dict(tickprefix="$", tickformat=",.0f"),
    yaxis2=dict(title="Orders", tickformat=","))
fig1.update_traces(hovertemplate=None)
figs["monthly_revenue"] = fig1

# 2. Channel CVR + Sessions (horizontal bar)
ch_sorted = channel.sort_values("cvr_pct", ascending=True)
fig2 = make_subplots(rows=1, cols=2, subplot_titles=("Sessions by Channel","Conversion Rate %"))
fig2.add_trace(go.Bar(y=ch_sorted["label"], x=ch_sorted["total_sessions"].astype(int),
    orientation="h", marker_color=C["teal"], name="Sessions",
    text=ch_sorted["total_sessions"].apply(lambda x: f"{int(x):,}"),
    textposition="outside"), row=1, col=1)
fig2.add_trace(go.Bar(y=ch_sorted["label"], x=ch_sorted["cvr_pct"],
    orientation="h", marker_color=[C["green"] if v >= ch_sorted["cvr_pct"].median()
                                    else C["amber"] for v in ch_sorted["cvr_pct"]],
    name="CVR %", text=[f"{v:.2f}%" for v in ch_sorted["cvr_pct"]],
    textposition="outside"), row=1, col=2)
fig2.update_layout(template=TEMPLATE, title="📡 Traffic Channel Performance",
    showlegend=False, height=320)
figs["channel_performance"] = fig2

# 3. Product Revenue Pie + Gross Profit Bar
fig3 = make_subplots(rows=1, cols=2, specs=[[{"type":"pie"},{"type":"bar"}]],
    subplot_titles=("Revenue Share","Gross Profit by Product"))
fig3.add_trace(go.Pie(labels=prod_agg["product_name"], values=prod_agg["revenue"],
    marker=dict(colors=PRODUCT_COLORS, line=dict(color="white",width=2)),
    textinfo="percent+label", hole=0.35, showlegend=False), row=1, col=1)
fig3.add_trace(go.Bar(x=prod_agg["product_name"], y=prod_agg["gp"],
    marker_color=PRODUCT_COLORS,
    text=[f"${v:,.0f}" for v in prod_agg["gp"]], textposition="outside",
    showlegend=False), row=1, col=2)
fig3.update_yaxes(tickprefix="$", tickformat=",.0f", row=1, col=2)
fig3.update_layout(template=TEMPLATE, title="🛍️ Product Revenue & Profitability", height=380)
figs["product_performance"] = fig3

# 4. Monthly Product Revenue Lines
prod_monthly = prod_items.groupby(["year_month","product_name"])["price_usd"].sum().reset_index()
fig4 = px.line(prod_monthly, x="year_month", y="price_usd", color="product_name",
    markers=True, color_discrete_sequence=PRODUCT_COLORS,
    title="📦 Monthly Revenue per Product",
    labels={"price_usd":"Revenue ($)","year_month":"Month","product_name":"Product"})
fig4.update_layout(template=TEMPLATE, xaxis_tickangle=-45,
    yaxis_tickprefix="$", yaxis_tickformat=",.0f",
    legend=dict(title="Product", orientation="h", y=1.1))
figs["product_trend"] = fig4

# 5. Refund Rate by Product
fig5 = make_subplots(rows=1, cols=2,
    subplot_titles=("Refund Rate %","Total Refunded ($)"))
ref_colors = [C["red"] if r > ref_agg["refund_rate"].mean() else C["green"]
              for r in ref_agg["refund_rate"]]
fig5.add_trace(go.Bar(x=ref_agg["product_name"], y=ref_agg["refund_rate"],
    marker_color=ref_colors, text=[f"{v:.1f}%" for v in ref_agg["refund_rate"]],
    textposition="outside", name="Refund Rate"), row=1, col=1)
fig5.add_shape(type="line", x0=-0.5, x1=len(ref_agg)-0.5,
    y0=ref_agg["refund_rate"].mean(), y1=ref_agg["refund_rate"].mean(),
    line=dict(color=C["grey"], dash="dash"), row=1, col=1)
fig5.add_trace(go.Bar(x=ref_agg["product_name"], y=ref_agg["refund_usd"],
    marker_color=ref_colors,
    text=[f"${v:,.0f}" for v in ref_agg["refund_usd"]], textposition="outside",
    name="Refund Amount"), row=1, col=2)
fig5.update_yaxes(tickprefix="$", tickformat=",.0f", row=1, col=2)
fig5.update_layout(template=TEMPLATE, title="🔄 Refund Analysis by Product",
    showlegend=False, height=360)
figs["refund_analysis"] = fig5

# 6. Device split – stacked area
dev_pivot = device.pivot(index="year_month", columns="device_type", values="sessions").fillna(0).reset_index()
fig6 = go.Figure()
dev_colors = [C["blue"], C["amber"]]
for i, col in enumerate([c for c in dev_pivot.columns if c != "year_month"]):
    color = dev_colors[i % len(dev_colors)]
    r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    fig6.add_trace(go.Scatter(x=dev_pivot["year_month"], y=dev_pivot[col],
        name=col.title(), stackgroup="one", mode="lines",
        line=dict(width=0.5), fillcolor=f"rgba({r},{g},{b},0.6)"))
fig6.update_layout(template=TEMPLATE, title="📱 Monthly Sessions by Device Type",
    xaxis_tickangle=-45, yaxis=dict(tickformat=","),
    legend=dict(orientation="h", y=1.1))
figs["device_sessions"] = fig6

# 7. CLV Distribution histogram
fig7 = go.Figure()
fig7.add_trace(go.Histogram(x=clv["lifetime_rev"], nbinsx=50,
    marker_color=C["purple"], opacity=0.8, name="Customers"))
fig7.add_vline(x=clv["lifetime_rev"].median(), line_dash="dash",
    line_color=C["red"], annotation_text=f"Median ${clv['lifetime_rev'].median():.0f}")
fig7.add_vline(x=clv["lifetime_rev"].mean(), line_dash="dot",
    line_color=C["amber"], annotation_text=f"Mean ${clv['lifetime_rev'].mean():.0f}")
fig7.update_layout(template=TEMPLATE, title="👥 Customer Lifetime Value Distribution",
    xaxis=dict(title="Lifetime Revenue ($)", tickprefix="$", tickformat=",.0f"),
    yaxis=dict(title="Customer Count"))
figs["clv_distribution"] = fig7

# 8. Cohort retention heatmap
orders_ch = orders.copy()
cohort_map = orders.groupby("user_id")["created_at"].min().dt.to_period("M").rename("cohort_month")
orders_ch  = orders_ch.join(cohort_map, on="user_id")
orders_ch["order_period"]  = orders_ch["created_at"].dt.to_period("M")
orders_ch["period_number"] = (orders_ch["order_period"] - orders_ch["cohort_month"]).apply(lambda x: x.n)
cohort_pivot = (orders_ch.groupby(["cohort_month","period_number"])["user_id"]
    .nunique().reset_index()
    .pivot(index="cohort_month", columns="period_number", values="user_id"))
cohort_pct   = cohort_pivot.divide(cohort_pivot[0], axis=0).mul(100).round(1)
ch_labels    = [[f"{v:.0f}%" if not np.isnan(v) else "" for v in row]
                for row in cohort_pct.iloc[:, :13].values]
fig8 = go.Figure(go.Heatmap(
    z=cohort_pct.iloc[:, :13].values,
    x=[f"M+{i}" for i in range(13)],
    y=cohort_pct.index.astype(str).tolist(),
    text=ch_labels, texttemplate="%{text}",
    colorscale="RdYlGn", reversescale=False,
    zmin=0, zmax=100,
    colorbar=dict(title="Retention %")))
fig8.update_layout(template=TEMPLATE, title="🔁 Monthly Cohort Retention Heatmap",
    xaxis=dict(title="Months Since First Purchase"),
    yaxis=dict(title="Cohort", autorange="reversed"),
    height=520)
figs["cohort_heatmap"] = fig8

# ═══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE HTML DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
print("🖥️   Assembling HTML dashboard…")

# KPI values
total_rev    = orders["price_usd"].sum()
total_orders = orders["order_id"].nunique()
avg_margin   = orders["margin_pct"].mean()
total_cust   = orders["user_id"].nunique()
overall_cvr  = total_orders / sessions["website_session_id"].nunique() * 100
refund_rate  = len(refunds) / len(items) * 100

# Build plotly HTML fragments (no <html> wrapper)
def fig_html(fig, div_id, height=None):
    if height:
        fig.update_layout(height=height)
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id)

plotly_cdn = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Maven Fuzzy Factory — E-Commerce Dashboard</title>
{plotly_cdn}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; background: #F1F5F9; color: #1e293b; }}

  /* HEADER */
  .header {{
    background: linear-gradient(135deg, #1e3a8a 0%, #2563EB 100%);
    color: white; padding: 28px 40px; display: flex;
    align-items: center; justify-content: space-between;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3);
  }}
  .header h1 {{ font-size: 1.6rem; font-weight: 700; }}
  .header p  {{ font-size: 0.85rem; opacity: 0.8; margin-top: 4px; }}
  .header .badge {{ background: rgba(255,255,255,0.15); border-radius: 20px;
    padding: 4px 12px; font-size: 0.75rem; margin-left: 8px; }}

  /* LAYOUT */
  .container {{ max-width: 1400px; margin: 0 auto; padding: 28px 24px; }}
  .section-title {{
    font-size: 1.05rem; font-weight: 700; color: #1e293b;
    margin: 32px 0 12px; border-left: 4px solid #2563EB;
    padding-left: 10px; text-transform: uppercase; letter-spacing: .05em;
  }}

  /* KPI CARDS */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; }}
  @media(max-width:1100px) {{ .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
  @media(max-width:680px)  {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  .kpi-card {{
    background: white; border-radius: 12px; padding: 20px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
    border-top: 4px solid var(--accent, #2563EB);
    transition: transform .15s, box-shadow .15s;
  }}
  .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.1); }}
  .kpi-value {{ font-size: 1.75rem; font-weight: 700; color: var(--accent, #2563EB); }}
  .kpi-label {{ font-size: 0.75rem; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing:.05em; }}

  /* CHART CARDS */
  .chart-card {{
    background: white; border-radius: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden;
    margin-bottom: 20px;
  }}
  .chart-card .chart-inner {{ padding: 4px 8px 8px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media(max-width:820px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

  /* FOOTER */
  footer {{
    text-align: center; padding: 24px; font-size: 0.78rem; color: #94a3b8;
    border-top: 1px solid #e2e8f0; margin-top: 32px;
  }}
  footer a {{ color: #2563EB; text-decoration: none; }}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div>
    <h1>🛒 Maven Fuzzy Factory — E-Commerce Analytics</h1>
    <p>Mar 2012 → Mar 2015 &nbsp;|&nbsp; Sales · Traffic · Products · Customers</p>
  </div>
  <div>
    <span class="badge">SQL + Python</span>
    <span class="badge">Power BI</span>
    <span class="badge">New Grad Portfolio</span>
  </div>
</div>

<div class="container">

<!-- KPI CARDS -->
<div class="section-title">Key Performance Indicators</div>
<div class="kpi-grid">
  <div class="kpi-card" style="--accent:#2563EB">
    <div class="kpi-value">${total_rev/1e6:.2f}M</div>
    <div class="kpi-label">Total Revenue</div>
  </div>
  <div class="kpi-card" style="--accent:#16A34A">
    <div class="kpi-value">{total_orders:,}</div>
    <div class="kpi-label">Total Orders</div>
  </div>
  <div class="kpi-card" style="--accent:#7C3AED">
    <div class="kpi-value">{total_cust:,}</div>
    <div class="kpi-label">Unique Customers</div>
  </div>
  <div class="kpi-card" style="--accent:#D97706">
    <div class="kpi-value">{overall_cvr:.2f}%</div>
    <div class="kpi-label">Overall CVR</div>
  </div>
  <div class="kpi-card" style="--accent:#0D9488">
    <div class="kpi-value">{avg_margin:.1f}%</div>
    <div class="kpi-label">Avg Gross Margin</div>
  </div>
  <div class="kpi-card" style="--accent:#DC2626">
    <div class="kpi-value">{refund_rate:.2f}%</div>
    <div class="kpi-label">Refund Rate</div>
  </div>
</div>

<!-- REVENUE TREND -->
<div class="section-title">Revenue & Sales Performance</div>
<div class="chart-card">
  <div class="chart-inner">{fig_html(figs["monthly_revenue"], "fig1", 420)}</div>
</div>

<!-- PRODUCT PERFORMANCE -->
<div class="section-title">Product Performance</div>
<div class="chart-card">
  <div class="chart-inner">{fig_html(figs["product_performance"], "fig3", 380)}</div>
</div>
<div class="chart-card">
  <div class="chart-inner">{fig_html(figs["product_trend"], "fig4", 360)}</div>
</div>

<!-- TRAFFIC & CHANNELS -->
<div class="section-title">Traffic & Marketing Channels</div>
<div class="chart-card">
  <div class="chart-inner">{fig_html(figs["channel_performance"], "fig2", 340)}</div>
</div>
<div class="chart-card">
  <div class="chart-inner">{fig_html(figs["device_sessions"], "fig6", 340)}</div>
</div>

<!-- CUSTOMER ANALYTICS -->
<div class="section-title">Customer Behavior & Lifetime Value</div>
<div class="grid-2">
  <div class="chart-card">
    <div class="chart-inner">{fig_html(figs["clv_distribution"], "fig7", 360)}</div>
  </div>
  <div class="chart-card">
    <div class="chart-inner">{fig_html(figs["refund_analysis"], "fig5", 360)}</div>
  </div>
</div>

<!-- COHORT HEATMAP -->
<div class="section-title">Cohort Retention</div>
<div class="chart-card">
  <div class="chart-inner">{fig_html(figs["cohort_heatmap"], "fig8", 520)}</div>
</div>

</div><!-- /container -->

<footer>
  Built by <a href="https://github.com/binhpham-2002" target="_blank">Binh Pham</a> &nbsp;|&nbsp;
  Dataset: Maven Analytics — Maven Fuzzy Factory &nbsp;|&nbsp;
  Stack: Python · Plotly · SQL · Power BI
</footer>
</body>
</html>"""

out_path = os.path.join(OUT, "ecommerce_dashboard.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅  Dashboard → {out_path}")

# ── Save static PNG screenshots for README ─────────────────────────────────────
print("\n📸  Saving PNG screenshots…")
try:
    import plotly.io as pio
    screenshots = {
        "01_monthly_revenue":    (figs["monthly_revenue"],    420),
        "02_channel_cvr":        (figs["channel_performance"],340),
        "03_product_performance":(figs["product_performance"],400),
        "04_cohort_heatmap":     (figs["cohort_heatmap"],     540),
        "05_clv_distribution":   (figs["clv_distribution"],   360),
        "06_device_sessions":    (figs["device_sessions"],    340),
    }
    for name, (fig, h) in screenshots.items():
        fig.update_layout(height=h, width=1000)
        path = os.path.join(SS_DIR, f"{name}.png")
        pio.write_image(fig, path, scale=1.5)
        print(f"  ✔  {name}.png")
except Exception as e:
    print(f"  ⚠  PNG export skipped ({e}) — HTML dashboard still works fine")

print("\n🎉  All done!")
print(f"   Open in browser: {out_path}")

# 🛒 E-Commerce Sales & Customer Analysis
### Maven Fuzzy Factory — End-to-End Data Analytics Portfolio

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-MySQL-4479A1?logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-F37626?logo=jupyter&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Project Overview

This project delivers a **full-stack data analysis** of **Maven Fuzzy Factory**, a fictional e-commerce retailer selling plush toys. Starting from raw transactional data, this analysis covers traffic attribution, revenue performance, product profitability, customer lifetime value, and refund quality — mirroring the analytics workflow of a professional data analyst role.

| Metric | Value |
|---|---|
| 📦 Total Orders | 32,313 |
| 💵 Total Revenue | ~$2.6M |
| 👥 Unique Customers | 31,696 |
| 📡 Website Sessions | 472,871 |
| 🔄 Total Refunds | 1,731 |
| 📅 Date Range | Mar 2012 – Mar 2015 |

---

## 🗂️ Repository Structure

```
ecommerce-sales-customer-analysis/
│
├── data/
│   ├── raw/                          # Original source CSVs (6 tables)
│   └── processed/                    # Cleaned & enriched CSVs
│
├── sql/                              # SQL analytical queries
│   ├── 01_traffic_channel_analysis.sql
│   ├── 02_sales_performance.sql
│   ├── 03_product_analysis.sql
│   ├── 04_customer_behavior.sql
│   └── 05_refund_analysis.sql
│
├── notebooks/                        # Jupyter EDA notebooks
│   ├── 01_data_cleaning_eda.ipynb
│   ├── 02_traffic_channel_analysis.ipynb
│   ├── 03_sales_product_analysis.ipynb
│   └── 04_customer_behavior_clv.ipynb
│
├── scripts/                          # Reusable Python scripts
│   ├── data_cleaning.py              # Full cleaning pipeline
│   └── export_powerbi.py             # Aggregated Power BI exports
│
├── powerbi/
│   └── dashboard_data/               # Pre-aggregated CSVs for Power BI
│
└── requirements.txt
```

---

## 🗄️ Data Schema

```
website_sessions ──┐
                   ├──> orders ──> order_items ──> order_item_refunds
website_pageviews ─┘                    │
                                        └──> products
```

| Table | Rows | Description |
|---|---|---|
| `website_sessions` | 472,871 | Sessions with UTM/device metadata |
| `website_pageviews` | 1,173,219 | Page-level browsing data |
| `orders` | 32,313 | Order-level revenue & COGS |
| `order_items` | 40,025 | SKU-level line items |
| `order_item_refunds` | 1,731 | Refund transactions |
| `products` | 4 | Product catalogue |

---

## 📊 Analysis Modules

### 1 · Traffic & Channel Analysis (`sql/01`, `notebooks/02`)
- Session volume by UTM source / campaign
- Session → order **conversion rate** by channel
- Device type split (desktop vs. mobile) and CVR impact
- New vs. repeat visitor conversion comparison
- Monthly session trend by traffic source
- Top landing pages

### 2 · Sales Performance (`sql/02`, `notebooks/03`)
- Monthly and quarterly **revenue & gross profit trends**
- Gross margin % tracking over time
- Net revenue after refunds
- AOV (Average Order Value) by channel

### 3 · Product Analysis (`sql/03`, `notebooks/03`)
- Per-product revenue, COGS, and margin
- Product launch timeline and post-launch sales ramp
- **Cross-sell analysis** (which products are ordered together)
- Refund rate per product and monthly refund trend

### 4 · Customer Behavior & CLV (`sql/04`, `notebooks/04`)
- **Customer Lifetime Value (CLV) distribution**
- Pareto: top 20% customer revenue contribution
- **Monthly cohort retention heatmap**
- Purchase frequency distribution
- CLV by acquisition channel

### 5 · Refund Analysis (`sql/05`)
- Overall refund rate and refund revenue impact
- Days-to-refund per product (speed of returns)
- Refund quality by traffic channel

---

## 🔑 Key Findings

1. **gsearch / nonbrand** drives the majority of sessions (~62%) but has a lower CVR than branded search — a clear signal to invest in brand campaigns or landing page optimisation.

2. **Desktop converts at ~3× the rate of mobile**, despite mobile making up a significant share of sessions — a major UX optimisation opportunity.

3. **Revenue grew from ~$25K/month (2012) to ~$120K/month (2015)** — roughly 4× growth — with acceleration after Product 2 (Forever Love Bear) launched in Jan 2013.

4. **Top 20% of customers contribute ~60% of revenue** — highly concentrated CLV, suggesting a loyalty/retention programme would have strong ROI.

5. **Product 4 (Hudson River Mini Bear) has the highest refund rate** — worth investigating product quality or mismatch between marketing and customer expectations.

6. **Repeat buyers have a 25%+ higher Average Order Value** than new visitors, validating investment in retention over pure acquisition.

---

## ⚙️ How to Run

### Prerequisites
```bash
pip install -r requirements.txt
```

### 1. Clean the data
```bash
python scripts/data_cleaning.py
```

### 2. Export Power BI-ready tables
```bash
python scripts/export_powerbi.py
```

### 3. Run notebooks
```bash
jupyter lab notebooks/
```
Open notebooks in order `01 → 04` for the full analytical story.

### 4. SQL queries
Connect to any MySQL-compatible database, import the raw CSVs, and run queries from the `sql/` folder in numbered order.

---

## 🖥️ Power BI Dashboard

The `powerbi/dashboard_data/` folder contains seven pre-aggregated CSVs ready to load into Power BI:

| File | Contents |
|---|---|
| `pbi_monthly_revenue.csv` | Revenue, profit, MoM growth |
| `pbi_channel_performance.csv` | Sessions, CVR, revenue by channel |
| `pbi_product_performance.csv` | Monthly units & revenue per product |
| `pbi_refund_by_product.csv` | Refund rate & amounts per product |
| `pbi_device_sessions.csv` | Monthly sessions by device type |
| `pbi_top_pages.csv` | Page view & session counts |
| `pbi_customer_clv.csv` | CLV, order frequency per customer |

**Recommended visuals:** KPI cards (revenue, orders, CVR), line chart (monthly trend), bar chart (channel CVR), matrix (cohort retention), scatter (CLV vs. orders).

---

## 🛠️ Tech Stack

- **Python 3.10+** — pandas, NumPy, Matplotlib, Seaborn
- **SQL (MySQL dialect)** — window functions, CTEs, JOINs
- **Jupyter Lab** — interactive EDA & visualisation
- **Power BI** — executive-level dashboard

---

## 👤 Author

**Binh Pham** — Data Analyst (New Grad)
- GitHub: [@binhpham-2002](https://github.com/binhpham-2002)
- Email: phamducbinh141@gmail.com

---

*Dataset: Maven Analytics – Maven Fuzzy Factory*

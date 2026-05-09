"""
Generates all Jupyter notebooks for the Maven Fuzzy Factory analysis portfolio.
Run once: python3 notebooks/create_notebooks.py
"""
import nbformat as nbf
import os

NB_DIR = os.path.dirname(os.path.abspath(__file__))

def nb(cells):
    n = nbf.v4.new_notebook()
    n.cells = cells
    return n

def md(text): return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text)

# ═══════════════════════════════════════════════════════════════════════════
# NOTEBOOK 1 – Data Cleaning & EDA Overview
# ═══════════════════════════════════════════════════════════════════════════
nb1 = nb([
    md("# 🛒 Maven Fuzzy Factory – Data Cleaning & EDA\n"
       "> **Author:** Binh Pham | **Dataset:** Maven Fuzzy Factory (E-Commerce)\n\n"
       "This notebook covers data loading, cleaning, and an initial exploratory overview of all six tables."),
    code("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Styling
sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'figure.dpi': 120, 'figure.figsize': (12, 5),
                     'axes.titlesize': 14, 'axes.titleweight': 'bold'})

BASE = '..'
RAW  = f'{BASE}/data/raw'
PROC = f'{BASE}/data/processed'
"""),
    md("## 1. Load Raw Data"),
    code("""
orders    = pd.read_csv(f'{RAW}/orders.csv',            parse_dates=['created_at'])
items     = pd.read_csv(f'{RAW}/order_items.csv',       parse_dates=['created_at'])
refunds   = pd.read_csv(f'{RAW}/order_item_refunds.csv',parse_dates=['created_at'])
products  = pd.read_csv(f'{RAW}/products.csv',          parse_dates=['created_at'])
sessions  = pd.read_csv(f'{RAW}/website_sessions.csv',  parse_dates=['created_at'])

tables = {'orders': orders, 'order_items': items, 'refunds': refunds,
          'products': products, 'sessions': sessions}

for name, df in tables.items():
    print(f"{name:20s}  {df.shape[0]:>10,} rows  {df.shape[1]:>3} cols  "
          f"  nulls: {df.isnull().sum().sum()}")
"""),
    md("## 2. Cleaning Steps"),
    code("""
# Orders – derived columns
orders['year_month']   = orders['created_at'].dt.to_period('M').astype(str)
orders['quarter']      = orders['created_at'].dt.to_period('Q').astype(str)
orders['gross_profit'] = (orders['price_usd'] - orders['cogs_usd']).round(2)
orders['margin_pct']   = (orders['gross_profit'] / orders['price_usd'] * 100).round(2)

# Sessions – fill UTM nulls
sessions['utm_source']   = sessions['utm_source'].fillna('direct')
sessions['utm_campaign'] = sessions['utm_campaign'].fillna('none')
sessions['utm_content']  = sessions['utm_content'].fillna('none')
sessions['device_type']  = sessions['device_type'].str.lower().str.strip()
sessions['year_month']   = sessions['created_at'].dt.to_period('M').astype(str)

# Items
items['year_month']   = items['created_at'].dt.to_period('M').astype(str)
items['gross_profit'] = (items['price_usd'] - items['cogs_usd']).round(2)

print("✔  Cleaning complete")
print(f"Date range (orders): {orders['created_at'].min().date()} → {orders['created_at'].max().date()}")
print(f"Unique customers: {orders['user_id'].nunique():,}")
print(f"Total revenue: ${orders['price_usd'].sum():,.2f}")
"""),
    md("## 3. Schema at a Glance"),
    code("""
fig, axes = plt.subplots(2, 3, figsize=(16, 8))
axes = axes.flatten()

for ax, (name, df) in zip(axes, tables.items()):
    missing_pct = df.isnull().mean() * 100
    colors = ['#e74c3c' if v > 0 else '#2ecc71' for v in missing_pct]
    ax.barh(missing_pct.index, missing_pct.values, color=colors)
    ax.set_title(f'{name}  ({df.shape[0]:,} rows)')
    ax.set_xlabel('Missing %')
    ax.axvline(0, color='black', linewidth=0.5)

fig.suptitle('Missing Value Overview by Table', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_missing_values.png', bbox_inches='tight')
plt.show()
"""),
    md("## 4. Key Dataset Stats"),
    code("""
summary = {
    'Total Sessions':     f"{sessions.shape[0]:,}",
    'Total Orders':       f"{orders.shape[0]:,}",
    'Total Revenue':      f"${orders['price_usd'].sum():,.0f}",
    'Gross Profit':       f"${orders['gross_profit'].sum():,.0f}",
    'Avg Margin':         f"{orders['margin_pct'].mean():.1f}%",
    'Unique Customers':   f"{orders['user_id'].nunique():,}",
    'Total Refunds':      f"{refunds.shape[0]:,}",
    'Overall Refund Rate':f"{refunds.shape[0]/items.shape[0]*100:.2f}%",
    'Products':           str(products.shape[0]),
    'Date Range':         f"{orders['created_at'].min().date()} → {orders['created_at'].max().date()}"
}
for k, v in summary.items():
    print(f"  {k:<25} {v}")
"""),
])

# ═══════════════════════════════════════════════════════════════════════════
# NOTEBOOK 2 – Traffic & Channel Analysis
# ═══════════════════════════════════════════════════════════════════════════
nb2 = nb([
    md("# 📡 Traffic & Marketing Channel Analysis\n"
       "> **Author:** Binh Pham | Maven Fuzzy Factory\n\n"
       "Deep dive into where sessions come from, conversion rates, device split, and repeat visitor behaviour."),
    code("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings; warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'figure.dpi': 120, 'figure.figsize': (12, 5),
                     'axes.titlesize': 13, 'axes.titleweight': 'bold'})

BASE  = '..'
PROC  = f'{BASE}/data/processed'
sessions = pd.read_csv(f'{PROC}/cleaned_website_sessions.csv', parse_dates=['created_at'])
orders   = pd.read_csv(f'{PROC}/cleaned_orders.csv',           parse_dates=['created_at'])
master   = pd.read_csv(f'{PROC}/master_orders.csv',            parse_dates=['created_at'])
"""),
    md("## 1. Session Volume by Channel"),
    code("""
ch = sessions.groupby(['utm_source','utm_campaign']).agg(
    sessions=('website_session_id','nunique'),
    repeat_sessions=('is_repeat_session','sum')
).reset_index()
ch['repeat_rate'] = (ch['repeat_sessions'] / ch['sessions'] * 100).round(1)
ch['channel'] = ch['utm_source'].str.title() + ' / ' + ch['utm_campaign'].str.title()
ch = ch.sort_values('sessions', ascending=True)

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.barh(ch['channel'], ch['sessions'], color=sns.color_palette('muted', len(ch)))
ax.bar_label(bars, labels=[f"{v:,}" for v in ch['sessions']], padding=5)
ax.set_xlabel('Sessions')
ax.set_title('Total Sessions by Traffic Channel')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_sessions_by_channel.png', bbox_inches='tight')
plt.show()
ch[['channel','sessions','repeat_rate']].sort_values('sessions', ascending=False)
"""),
    md("## 2. Session-to-Order Conversion Rate by Channel"),
    code("""
sess_agg  = sessions.groupby(['utm_source','utm_campaign'])['website_session_id'].nunique().reset_index(name='total_sessions')
order_agg = master.groupby(['utm_source','utm_campaign'])['order_id'].nunique().reset_index(name='orders')
cvr = sess_agg.merge(order_agg, on=['utm_source','utm_campaign'], how='left').fillna(0)
cvr['cvr_pct'] = (cvr['orders'] / cvr['total_sessions'] * 100).round(2)
cvr['channel'] = cvr['utm_source'].str.title() + ' / ' + cvr['utm_campaign'].str.title()
cvr = cvr.sort_values('cvr_pct', ascending=False)

fig, ax = plt.subplots(figsize=(11, 4))
colors = ['#27ae60' if v > cvr['cvr_pct'].median() else '#e74c3c' for v in cvr['cvr_pct']]
bars = ax.bar(cvr['channel'], cvr['cvr_pct'], color=colors)
ax.bar_label(bars, labels=[f"{v:.1f}%" for v in cvr['cvr_pct']], padding=3)
ax.set_ylabel('Conversion Rate (%)')
ax.set_title('Session → Order Conversion Rate by Channel')
plt.xticks(rotation=25, ha='right')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_cvr_by_channel.png', bbox_inches='tight')
plt.show()
"""),
    md("## 3. Monthly Session Trend"),
    code("""
monthly = sessions.groupby(['year_month','utm_source'])['website_session_id'].nunique().reset_index(name='sessions')
pivot   = monthly.pivot(index='year_month', columns='utm_source', values='sessions').fillna(0)

fig, ax = plt.subplots(figsize=(14, 5))
pivot.plot(ax=ax, marker='o', linewidth=2)
ax.set_title('Monthly Sessions by Traffic Source')
ax.set_xlabel('Month')
ax.set_ylabel('Sessions')
ax.legend(title='Source', bbox_to_anchor=(1.01, 1))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_monthly_sessions.png', bbox_inches='tight')
plt.show()
"""),
    md("## 4. Device Type Split"),
    code("""
device = sessions.groupby('device_type')['website_session_id'].nunique()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].pie(device.values, labels=device.index, autopct='%1.1f%%',
            colors=['#3498db','#e67e22'], startangle=90,
            wedgeprops={'edgecolor':'white','linewidth':2})
axes[0].set_title('Session Share by Device Type')

# CVR by device
dev_cvr = sessions.merge(orders[['website_session_id','order_id']], on='website_session_id', how='left')
dev_cvr = dev_cvr.groupby('device_type').agg(
    sessions=('website_session_id','nunique'), orders=('order_id','nunique')
).reset_index()
dev_cvr['cvr'] = (dev_cvr['orders'] / dev_cvr['sessions'] * 100).round(2)
axes[1].bar(dev_cvr['device_type'], dev_cvr['cvr'], color=['#3498db','#e67e22'])
for i, row in dev_cvr.iterrows():
    axes[1].text(i, row['cvr'] + 0.1, f"{row['cvr']:.2f}%", ha='center', fontweight='bold')
axes[1].set_ylabel('Conversion Rate (%)')
axes[1].set_title('Conversion Rate by Device Type')

plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_device_split.png', bbox_inches='tight')
plt.show()
"""),
    md("## 5. New vs Repeat Visitor Revenue"),
    code("""
visitor = master.groupby('is_repeat_session').agg(
    orders=('order_id','nunique'),
    revenue=('price_usd','sum'),
    avg_order_val=('price_usd','mean')
).round(2).reset_index()
visitor['label'] = visitor['is_repeat_session'].map({0:'New Visitor', 1:'Repeat Visitor'})

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
metrics = [('orders','Orders'), ('revenue','Revenue ($)'), ('avg_order_val','Avg Order Value ($)')]
colors  = ['#9b59b6', '#1abc9c']
for ax, (col, title) in zip(axes, metrics):
    ax.bar(visitor['label'], visitor[col], color=colors)
    for i, v in enumerate(visitor[col]):
        ax.text(i, v + visitor[col].max()*0.01, f"{v:,.0f}", ha='center', fontweight='bold')
    ax.set_title(title)

fig.suptitle('New vs Repeat Visitor Comparison', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_new_vs_repeat.png', bbox_inches='tight')
plt.show()
"""),
])

# ═══════════════════════════════════════════════════════════════════════════
# NOTEBOOK 3 – Sales & Product Analysis
# ═══════════════════════════════════════════════════════════════════════════
nb3 = nb([
    md("# 💰 Sales Performance & Product Analysis\n"
       "> **Author:** Binh Pham | Maven Fuzzy Factory\n\n"
       "Revenue trends, gross profit, product-level performance, cross-sell, and refund analysis."),
    code("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings; warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'figure.dpi':120, 'figure.figsize':(12,5),
                     'axes.titlesize':13, 'axes.titleweight':'bold'})

BASE  = '..'
PROC  = f'{BASE}/data/processed'
orders   = pd.read_csv(f'{PROC}/cleaned_orders.csv',      parse_dates=['created_at'])
items    = pd.read_csv(f'{PROC}/cleaned_order_items.csv',  parse_dates=['created_at'])
refunds  = pd.read_csv(f'{PROC}/cleaned_order_item_refunds.csv', parse_dates=['created_at'])
products = pd.read_csv(f'{PROC}/cleaned_products.csv',    parse_dates=['created_at'])
master   = pd.read_csv(f'{PROC}/master_orders.csv',       parse_dates=['created_at'])
"""),
    md("## 1. Monthly Revenue & Gross Profit Trend"),
    code("""
monthly = orders.groupby('year_month').agg(
    revenue=('price_usd','sum'), gross_profit=('gross_profit','sum'),
    orders=('order_id','nunique')
).reset_index()

fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()
x = range(len(monthly))
ax1.bar(x, monthly['revenue'], alpha=0.7, color='#3498db', label='Revenue')
ax1.bar(x, monthly['gross_profit'], alpha=0.7, color='#27ae60', label='Gross Profit')
ax2.plot(x, monthly['orders'], color='#e74c3c', marker='o', linewidth=2, label='Orders')

ax1.set_xticks(x)
ax1.set_xticklabels(monthly['year_month'], rotation=45, ha='right', fontsize=8)
ax1.set_ylabel('USD ($)')
ax2.set_ylabel('Orders', color='#e74c3c')
ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f'${v:,.0f}'))
ax1.set_title('Monthly Revenue, Gross Profit & Order Volume')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_monthly_revenue.png', bbox_inches='tight')
plt.show()
"""),
    md("## 2. Product Revenue Share"),
    code("""
prod_rev = items.merge(products[['product_id','product_name']], on='product_id')
prod_agg = prod_rev.groupby('product_name').agg(
    revenue=('price_usd','sum'), units=('order_item_id','count'),
    gross_profit=('gross_profit','sum')
).reset_index().sort_values('revenue', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors = sns.color_palette('Set2', 4)
axes[0].pie(prod_agg['revenue'], labels=prod_agg['product_name'],
            autopct='%1.1f%%', colors=colors,
            wedgeprops={'edgecolor':'white','linewidth':2})
axes[0].set_title('Revenue Share by Product')

axes[1].bar(prod_agg['product_name'], prod_agg['gross_profit'], color=colors)
axes[1].set_ylabel('Gross Profit ($)')
axes[1].set_title('Gross Profit by Product')
axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda v,_: f'${v:,.0f}'))
for i, row in prod_agg.reset_index().iterrows():
    axes[1].text(i, row['gross_profit'] + 2000, f"${row['gross_profit']:,.0f}",
                 ha='center', fontsize=9, fontweight='bold')
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_product_revenue.png', bbox_inches='tight')
plt.show()
"""),
    md("## 3. Monthly Product Sales Trend"),
    code("""
prod_monthly = prod_rev.groupby(['year_month','product_name'])['price_usd'].sum().reset_index()
pivot = prod_monthly.pivot(index='year_month', columns='product_name', values='price_usd').fillna(0)

fig, ax = plt.subplots(figsize=(14, 5))
pivot.plot(ax=ax, marker='o', linewidth=2)
ax.set_title('Monthly Revenue per Product')
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v,_: f'${v:,.0f}'))
ax.set_xlabel('Month')
ax.set_ylabel('Revenue')
ax.legend(title='Product', bbox_to_anchor=(1.01, 1))
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_product_trend.png', bbox_inches='tight')
plt.show()
"""),
    md("## 4. Refund Rate by Product"),
    code("""
ref_merged = items.merge(refunds[['order_item_id','refund_amount_usd']], on='order_item_id', how='left')
ref_merged = ref_merged.merge(products[['product_id','product_name']], on='product_id')
ref_agg = ref_merged.groupby('product_name').agg(
    units_sold=('order_item_id','count'),
    refunds=('refund_amount_usd','count'),
    total_refunded=('refund_amount_usd','sum')
).reset_index()
ref_agg['refund_rate'] = (ref_agg['refunds'] / ref_agg['units_sold'] * 100).round(2)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
colors = ['#e74c3c' if r > ref_agg['refund_rate'].mean() else '#27ae60' for r in ref_agg['refund_rate']]
axes[0].bar(ref_agg['product_name'], ref_agg['refund_rate'], color=colors)
axes[0].axhline(ref_agg['refund_rate'].mean(), color='gray', linestyle='--', label='Average')
axes[0].set_ylabel('Refund Rate (%)')
axes[0].set_title('Refund Rate by Product')
for i, row in ref_agg.iterrows():
    axes[0].text(i, row['refund_rate'] + 0.1, f"{row['refund_rate']:.1f}%", ha='center', fontweight='bold')
plt.sca(axes[0]); plt.xticks(rotation=15, ha='right')

axes[1].bar(ref_agg['product_name'], ref_agg['total_refunded'], color=colors)
axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda v,_: f'${v:,.0f}'))
axes[1].set_title('Total Refund Amount by Product')
plt.sca(axes[1]); plt.xticks(rotation=15, ha='right')

plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_refund_by_product.png', bbox_inches='tight')
plt.show()
"""),
    md("## 5. Gross Margin % Over Time"),
    code("""
margin_trend = orders.groupby('year_month').agg(
    revenue=('price_usd','sum'), gross_profit=('gross_profit','sum')
).reset_index()
margin_trend['margin_pct'] = (margin_trend['gross_profit'] / margin_trend['revenue'] * 100).round(2)

fig, ax = plt.subplots(figsize=(14, 4))
ax.fill_between(range(len(margin_trend)), margin_trend['margin_pct'], alpha=0.3, color='#9b59b6')
ax.plot(range(len(margin_trend)), margin_trend['margin_pct'], color='#9b59b6', linewidth=2, marker='o')
ax.axhline(margin_trend['margin_pct'].mean(), color='red', linestyle='--', label=f"Avg {margin_trend['margin_pct'].mean():.1f}%")
ax.set_xticks(range(len(margin_trend)))
ax.set_xticklabels(margin_trend['year_month'], rotation=45, ha='right', fontsize=8)
ax.set_ylabel('Gross Margin (%)')
ax.set_title('Monthly Gross Margin %')
ax.legend()
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_margin_trend.png', bbox_inches='tight')
plt.show()
"""),
])

# ═══════════════════════════════════════════════════════════════════════════
# NOTEBOOK 4 – Customer Behavior & CLV
# ═══════════════════════════════════════════════════════════════════════════
nb4 = nb([
    md("# 👥 Customer Behavior & Lifetime Value\n"
       "> **Author:** Binh Pham | Maven Fuzzy Factory\n\n"
       "Customer segmentation, cohort retention, CLV distribution, and funnel analysis."),
    code("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings; warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'figure.dpi':120, 'figure.figsize':(12,5),
                     'axes.titlesize':13, 'axes.titleweight':'bold'})

BASE  = '..'
PROC  = f'{BASE}/data/processed'
orders   = pd.read_csv(f'{PROC}/cleaned_orders.csv',     parse_dates=['created_at'])
sessions = pd.read_csv(f'{PROC}/cleaned_website_sessions.csv', parse_dates=['created_at'])
master   = pd.read_csv(f'{PROC}/master_orders.csv',      parse_dates=['created_at'])
"""),
    md("## 1. Customer Lifetime Value Distribution"),
    code("""
clv = master.groupby('user_id').agg(
    total_orders=('order_id','nunique'),
    lifetime_rev=('price_usd','sum')
).reset_index()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].hist(clv['lifetime_rev'], bins=40, color='#3498db', edgecolor='white')
axes[0].axvline(clv['lifetime_rev'].median(), color='red', linestyle='--',
                label=f"Median: ${clv['lifetime_rev'].median():.2f}")
axes[0].axvline(clv['lifetime_rev'].mean(), color='orange', linestyle='--',
                label=f"Mean: ${clv['lifetime_rev'].mean():.2f}")
axes[0].set_xlabel('Lifetime Revenue ($)')
axes[0].set_ylabel('Customer Count')
axes[0].set_title('Customer Lifetime Value Distribution')
axes[0].legend()

order_counts = clv['total_orders'].value_counts().sort_index()
axes[1].bar(order_counts.index, order_counts.values, color='#27ae60')
axes[1].set_xlabel('Total Orders per Customer')
axes[1].set_ylabel('Number of Customers')
axes[1].set_title('Purchase Frequency Distribution')

plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_clv_distribution.png', bbox_inches='tight')
plt.show()

print(f"Single-purchase customers: {(clv['total_orders']==1).sum():,} ({(clv['total_orders']==1).mean()*100:.1f}%)")
print(f"Repeat buyers:             {(clv['total_orders']>1).sum():,} ({(clv['total_orders']>1).mean()*100:.1f}%)")
"""),
    md("## 2. Revenue Contribution: Top 20% vs Bottom 80% (Pareto)"),
    code("""
clv_sorted = clv.sort_values('lifetime_rev', ascending=False).reset_index(drop=True)
clv_sorted['cumulative_rev']   = clv_sorted['lifetime_rev'].cumsum()
clv_sorted['cumulative_rev_pct'] = clv_sorted['cumulative_rev'] / clv_sorted['lifetime_rev'].sum() * 100
clv_sorted['customer_pct']     = (clv_sorted.index + 1) / len(clv_sorted) * 100

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(clv_sorted['customer_pct'], clv_sorted['cumulative_rev_pct'],
        color='#9b59b6', linewidth=2)
ax.axhline(80, color='red', linestyle='--', alpha=0.7, label='80% Revenue')
ax.fill_between(clv_sorted['customer_pct'], clv_sorted['cumulative_rev_pct'], alpha=0.2, color='#9b59b6')
ax.set_xlabel('Customers (%)')
ax.set_ylabel('Cumulative Revenue (%)')
ax.set_title('Pareto Chart: Customer Revenue Concentration')
ax.legend()
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_pareto.png', bbox_inches='tight')
plt.show()

top20_rev = clv_sorted[clv_sorted['customer_pct'] <= 20]['lifetime_rev'].sum()
print(f"Top 20% of customers → {top20_rev / clv['lifetime_rev'].sum()*100:.1f}% of revenue")
"""),
    md("## 3. Cohort Retention Heatmap"),
    code("""
orders_sorted = orders.sort_values('created_at')
cohort = orders.groupby('user_id')['created_at'].min().dt.to_period('M').rename('cohort_month')
orders_ch = orders.join(cohort, on='user_id')
orders_ch['order_month'] = orders_ch['created_at'].dt.to_period('M')
orders_ch['periods']     = (orders_ch['order_month'] - orders_ch['cohort_month']).apply(lambda x: x.n)

cohort_data = orders_ch.groupby(['cohort_month','periods'])['user_id'].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index='cohort_month', columns='periods', values='user_id')
cohort_pct   = cohort_pivot.divide(cohort_pivot[0], axis=0) * 100

fig, ax = plt.subplots(figsize=(16, 8))
sns.heatmap(cohort_pct.iloc[:, :13], annot=True, fmt='.0f', cmap='YlOrRd_r',
            linewidths=0.5, ax=ax, cbar_kws={'label':'Retention %'})
ax.set_title('Monthly Cohort Retention Heatmap (%)', fontsize=14, fontweight='bold')
ax.set_xlabel('Months Since First Purchase')
ax.set_ylabel('Cohort Month')
plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_cohort_heatmap.png', bbox_inches='tight')
plt.show()
"""),
    md("## 4. CLV by Acquisition Channel"),
    code("""
ch_clv = master.groupby(['user_id','utm_source']).agg(
    lifetime_rev=('price_usd','sum'), orders=('order_id','nunique')
).reset_index()
ch_summary = ch_clv.groupby('utm_source').agg(
    avg_clv=('lifetime_rev','mean'), median_clv=('lifetime_rev','median'),
    customers=('user_id','nunique'), total_rev=('lifetime_rev','sum')
).round(2).reset_index().sort_values('avg_clv', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
colors = sns.color_palette('Set2', len(ch_summary))
axes[0].bar(ch_summary['utm_source'], ch_summary['avg_clv'], color=colors)
axes[0].set_ylabel('Avg CLV ($)')
axes[0].set_title('Average Customer Lifetime Value by Channel')
for i, row in ch_summary.reset_index().iterrows():
    axes[0].text(i, row['avg_clv'] + 0.5, f"${row['avg_clv']:.1f}", ha='center', fontsize=9)

axes[1].bar(ch_summary['utm_source'], ch_summary['total_rev'], color=colors)
axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda v,_: f'${v/1e6:.1f}M'))
axes[1].set_title('Total Revenue by Acquisition Channel')

plt.tight_layout()
plt.savefig(f'{BASE}/notebooks/img_clv_by_channel.png', bbox_inches='tight')
plt.show()
print(ch_summary.to_string(index=False))
"""),
])

# ── Save notebooks ────────────────────────────────────────────────────────────
notebooks = [
    ('01_data_cleaning_eda.ipynb', nb1),
    ('02_traffic_channel_analysis.ipynb', nb2),
    ('03_sales_product_analysis.ipynb', nb3),
    ('04_customer_behavior_clv.ipynb', nb4),
]
for fname, notebook in notebooks:
    path = os.path.join(NB_DIR, fname)
    nbf.write(notebook, path)
    print(f"✔  {fname}")

print("\n✅  All notebooks created!")

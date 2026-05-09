-- =============================================================
-- 02_sales_performance.sql
-- Maven Fuzzy Factory | Revenue & Sales Performance Analysis
-- Author: Binh Pham | GitHub: binhpham-2002
-- =============================================================

-- ---------------------------------------------------------------
-- 1. Overall revenue & margin summary
-- ---------------------------------------------------------------
SELECT
    COUNT(DISTINCT order_id)                        AS total_orders,
    SUM(items_purchased)                            AS total_items_sold,
    ROUND(SUM(price_usd), 2)                        AS total_revenue,
    ROUND(SUM(cogs_usd), 2)                         AS total_cogs,
    ROUND(SUM(price_usd) - SUM(cogs_usd), 2)        AS gross_profit,
    ROUND(100.0 * (SUM(price_usd) - SUM(cogs_usd))
          / SUM(price_usd), 2)                      AS gross_margin_pct,
    ROUND(AVG(price_usd), 2)                        AS avg_order_value
FROM orders;


-- ---------------------------------------------------------------
-- 2. Monthly revenue trend
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(created_at, '%Y-%m')  AS yr_month,
    COUNT(DISTINCT order_id)          AS orders,
    ROUND(SUM(price_usd), 2)          AS revenue,
    ROUND(SUM(price_usd) - SUM(cogs_usd), 2) AS gross_profit,
    ROUND(AVG(price_usd), 2)          AS avg_order_value
FROM orders
GROUP BY yr_month
ORDER BY yr_month;


-- ---------------------------------------------------------------
-- 3. Revenue by primary product
-- ---------------------------------------------------------------
SELECT
    o.primary_product_id,
    p.product_name,
    COUNT(DISTINCT o.order_id)               AS orders,
    ROUND(SUM(o.price_usd), 2)               AS revenue,
    ROUND(SUM(o.price_usd - o.cogs_usd), 2) AS gross_profit,
    ROUND(100.0 * (SUM(o.price_usd) - SUM(o.cogs_usd))
          / SUM(o.price_usd), 2)             AS margin_pct
FROM orders o
JOIN products p ON o.primary_product_id = p.product_id
GROUP BY o.primary_product_id, p.product_name
ORDER BY revenue DESC;


-- ---------------------------------------------------------------
-- 4. Multi-item vs single-item order split
-- ---------------------------------------------------------------
SELECT
    items_purchased,
    COUNT(order_id)                                AS orders,
    ROUND(100.0 * COUNT(order_id)
          / SUM(COUNT(order_id)) OVER (), 2)       AS pct_of_orders,
    ROUND(SUM(price_usd), 2)                       AS revenue,
    ROUND(AVG(price_usd), 2)                       AS avg_order_value
FROM orders
GROUP BY items_purchased
ORDER BY items_purchased;


-- ---------------------------------------------------------------
-- 5. Quarterly revenue growth
-- ---------------------------------------------------------------
SELECT
    YEAR(created_at)    AS yr,
    QUARTER(created_at) AS qtr,
    COUNT(order_id)     AS orders,
    ROUND(SUM(price_usd), 2)   AS revenue,
    ROUND(SUM(price_usd) - LAG(SUM(price_usd))
          OVER (ORDER BY YEAR(created_at), QUARTER(created_at)), 2) AS qoq_revenue_change
FROM orders
GROUP BY yr, qtr
ORDER BY yr, qtr;


-- ---------------------------------------------------------------
-- 6. Revenue after accounting for refunds (net revenue)
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(o.created_at, '%Y-%m')            AS yr_month,
    ROUND(SUM(o.price_usd), 2)                    AS gross_revenue,
    ROUND(COALESCE(SUM(r.refund_amount_usd), 0), 2) AS total_refunds,
    ROUND(SUM(o.price_usd)
          - COALESCE(SUM(r.refund_amount_usd), 0), 2) AS net_revenue
FROM orders o
LEFT JOIN (
    SELECT order_id, SUM(refund_amount_usd) AS refund_amount_usd
    FROM order_item_refunds
    GROUP BY order_id
) r ON o.order_id = r.order_id
GROUP BY yr_month
ORDER BY yr_month;

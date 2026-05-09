-- =============================================================
-- 03_product_analysis.sql
-- Maven Fuzzy Factory | Product Performance & Cross-sell Analysis
-- Author: Binh Pham | GitHub: binhpham-2002
-- =============================================================

-- ---------------------------------------------------------------
-- 1. Product-level performance summary
-- ---------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    COUNT(oi.order_item_id)                          AS units_sold,
    ROUND(SUM(oi.price_usd), 2)                      AS revenue,
    ROUND(SUM(oi.cogs_usd), 2)                       AS cogs,
    ROUND(SUM(oi.price_usd - oi.cogs_usd), 2)        AS gross_profit,
    ROUND(100.0 * (SUM(oi.price_usd) - SUM(oi.cogs_usd))
          / SUM(oi.price_usd), 2)                    AS margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY revenue DESC;


-- ---------------------------------------------------------------
-- 2. Product launch timeline & cumulative sales
-- ---------------------------------------------------------------
SELECT
    p.product_name,
    DATE_FORMAT(p.created_at, '%Y-%m-%d')            AS launch_date,
    DATE_FORMAT(oi.created_at, '%Y-%m')              AS sale_month,
    COUNT(oi.order_item_id)                          AS units_sold,
    ROUND(SUM(oi.price_usd), 2)                      AS monthly_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_name, launch_date, sale_month
ORDER BY p.product_id, sale_month;


-- ---------------------------------------------------------------
-- 3. Cross-sell analysis: which products are ordered together
-- ---------------------------------------------------------------
SELECT
    p1.product_name   AS primary_product,
    p2.product_name   AS cross_sell_product,
    COUNT(*)          AS times_paired
FROM order_items oi1
JOIN order_items oi2
    ON oi1.order_id = oi2.order_id
    AND oi1.product_id <> oi2.product_id
    AND oi1.is_primary_item = 1
JOIN products p1 ON oi1.product_id = p1.product_id
JOIN products p2 ON oi2.product_id = p2.product_id
GROUP BY p1.product_name, p2.product_name
ORDER BY times_paired DESC;


-- ---------------------------------------------------------------
-- 4. Refund rate by product
-- ---------------------------------------------------------------
SELECT
    p.product_name,
    COUNT(oi.order_item_id)                          AS units_sold,
    COUNT(r.order_item_refund_id)                    AS units_refunded,
    ROUND(100.0 * COUNT(r.order_item_refund_id)
          / COUNT(oi.order_item_id), 2)              AS refund_rate_pct,
    ROUND(SUM(r.refund_amount_usd), 2)               AS total_refunded_usd
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN order_item_refunds r ON oi.order_item_id = r.order_item_id
GROUP BY p.product_name
ORDER BY refund_rate_pct DESC;


-- ---------------------------------------------------------------
-- 5. Monthly refund rate trend per product
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(oi.created_at, '%Y-%m')              AS yr_month,
    p.product_name,
    COUNT(oi.order_item_id)                          AS units_sold,
    COUNT(r.order_item_refund_id)                    AS refunds,
    ROUND(100.0 * COUNT(r.order_item_refund_id)
          / COUNT(oi.order_item_id), 2)              AS refund_rate_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN order_item_refunds r ON oi.order_item_id = r.order_item_id
GROUP BY yr_month, p.product_name
ORDER BY yr_month, p.product_name;

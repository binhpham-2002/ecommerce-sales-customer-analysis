-- =============================================================
-- 05_refund_analysis.sql
-- Maven Fuzzy Factory | Refund & Returns Analysis
-- Author: Binh Pham | GitHub: binhpham-2002
-- =============================================================

-- ---------------------------------------------------------------
-- 1. Overall refund summary
-- ---------------------------------------------------------------
SELECT
    COUNT(DISTINCT r.order_item_refund_id)           AS total_refunds,
    COUNT(DISTINCT oi.order_item_id)                 AS total_items_sold,
    ROUND(100.0 * COUNT(DISTINCT r.order_item_refund_id)
          / COUNT(DISTINCT oi.order_item_id), 2)     AS overall_refund_rate_pct,
    ROUND(SUM(r.refund_amount_usd), 2)               AS total_refund_amount,
    ROUND(SUM(oi.price_usd), 2)                      AS total_revenue,
    ROUND(100.0 * SUM(r.refund_amount_usd)
          / SUM(oi.price_usd), 2)                    AS refund_revenue_pct
FROM order_items oi
LEFT JOIN order_item_refunds r ON oi.order_item_id = r.order_item_id;


-- ---------------------------------------------------------------
-- 2. Monthly refund trend
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(r.created_at, '%Y-%m')   AS refund_month,
    COUNT(r.order_item_refund_id)        AS refunds,
    ROUND(SUM(r.refund_amount_usd), 2)   AS refund_amount
FROM order_item_refunds r
GROUP BY refund_month
ORDER BY refund_month;


-- ---------------------------------------------------------------
-- 3. Days between order and refund (speed of returns)
-- ---------------------------------------------------------------
SELECT
    p.product_name,
    ROUND(AVG(DATEDIFF(r.created_at, oi.created_at)), 1) AS avg_days_to_refund,
    MIN(DATEDIFF(r.created_at, oi.created_at))           AS min_days,
    MAX(DATEDIFF(r.created_at, oi.created_at))           AS max_days
FROM order_item_refunds r
JOIN order_items oi ON r.order_item_id = oi.order_item_id
JOIN products p     ON oi.product_id   = p.product_id
GROUP BY p.product_name
ORDER BY avg_days_to_refund;


-- ---------------------------------------------------------------
-- 4. Refund rate by traffic channel (quality of customers)
-- ---------------------------------------------------------------
SELECT
    ws.utm_source,
    ws.utm_campaign,
    COUNT(DISTINCT oi.order_item_id)                         AS items_sold,
    COUNT(DISTINCT r.order_item_refund_id)                   AS refunds,
    ROUND(100.0 * COUNT(DISTINCT r.order_item_refund_id)
          / COUNT(DISTINCT oi.order_item_id), 2)             AS refund_rate_pct
FROM website_sessions ws
JOIN orders o   ON ws.website_session_id = o.website_session_id
JOIN order_items oi ON o.order_id        = oi.order_id
LEFT JOIN order_item_refunds r ON oi.order_item_id = r.order_item_id
GROUP BY ws.utm_source, ws.utm_campaign
ORDER BY refund_rate_pct DESC;

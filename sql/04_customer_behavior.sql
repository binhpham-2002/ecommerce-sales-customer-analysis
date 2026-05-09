-- =============================================================
-- 04_customer_behavior.sql
-- Maven Fuzzy Factory | Customer Segmentation & Behavior Analysis
-- Author: Binh Pham | GitHub: binhpham-2002
-- =============================================================

-- ---------------------------------------------------------------
-- 1. Customer lifetime value (CLV) distribution
-- ---------------------------------------------------------------
SELECT
    user_id,
    COUNT(DISTINCT order_id)         AS total_orders,
    ROUND(SUM(price_usd), 2)         AS lifetime_revenue,
    ROUND(AVG(price_usd), 2)         AS avg_order_value,
    MIN(created_at)                  AS first_order_date,
    MAX(created_at)                  AS last_order_date,
    DATEDIFF(MAX(created_at), MIN(created_at)) AS days_active
FROM orders
GROUP BY user_id
ORDER BY lifetime_revenue DESC
LIMIT 20;


-- ---------------------------------------------------------------
-- 2. Cohort analysis: first purchase month & retention
-- ---------------------------------------------------------------
WITH cohort AS (
    SELECT
        user_id,
        DATE_FORMAT(MIN(created_at), '%Y-%m') AS cohort_month
    FROM orders
    GROUP BY user_id
),
user_orders AS (
    SELECT
        o.user_id,
        DATE_FORMAT(o.created_at, '%Y-%m')  AS order_month,
        c.cohort_month
    FROM orders o
    JOIN cohort c ON o.user_id = c.user_id
)
SELECT
    cohort_month,
    order_month,
    COUNT(DISTINCT user_id) AS active_users
FROM user_orders
GROUP BY cohort_month, order_month
ORDER BY cohort_month, order_month;


-- ---------------------------------------------------------------
-- 3. Repeat purchase rate by acquisition channel
-- ---------------------------------------------------------------
SELECT
    ws.utm_source,
    ws.utm_campaign,
    COUNT(DISTINCT ws.user_id)                          AS total_users,
    COUNT(DISTINCT CASE WHEN o2.user_id IS NOT NULL
                         THEN ws.user_id END)           AS repeat_buyers,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN o2.user_id IS NOT NULL
                                       THEN ws.user_id END)
          / COUNT(DISTINCT ws.user_id), 2)              AS repeat_rate_pct
FROM website_sessions ws
LEFT JOIN orders o1 ON ws.website_session_id = o1.website_session_id
LEFT JOIN (
    SELECT user_id, COUNT(order_id) AS order_count
    FROM orders
    GROUP BY user_id
    HAVING order_count > 1
) o2 ON ws.user_id = o2.user_id
WHERE o1.order_id IS NOT NULL   -- only users who purchased at least once
GROUP BY ws.utm_source, ws.utm_campaign
ORDER BY repeat_rate_pct DESC;


-- ---------------------------------------------------------------
-- 4. Session funnel: sessions → pageviews → orders
-- ---------------------------------------------------------------
SELECT
    COUNT(DISTINCT ws.website_session_id)                AS total_sessions,
    COUNT(DISTINCT pv.website_session_id)                AS sessions_with_pageviews,
    COUNT(DISTINCT o.website_session_id)                 AS sessions_with_orders,
    ROUND(100.0 * COUNT(DISTINCT o.website_session_id)
          / COUNT(DISTINCT ws.website_session_id), 2)    AS overall_cvr_pct
FROM website_sessions ws
LEFT JOIN website_pageviews pv ON ws.website_session_id = pv.website_session_id
LEFT JOIN orders o              ON ws.website_session_id = o.website_session_id;


-- ---------------------------------------------------------------
-- 5. Average pages viewed per session by device type
-- ---------------------------------------------------------------
SELECT
    ws.device_type,
    COUNT(DISTINCT ws.website_session_id)                    AS sessions,
    COUNT(pv.website_pageview_id)                            AS total_pageviews,
    ROUND(COUNT(pv.website_pageview_id)
          / COUNT(DISTINCT ws.website_session_id), 2)        AS avg_pages_per_session
FROM website_sessions ws
LEFT JOIN website_pageviews pv ON ws.website_session_id = pv.website_session_id
GROUP BY ws.device_type;


-- ---------------------------------------------------------------
-- 6. Most visited pages overall
-- ---------------------------------------------------------------
SELECT
    pageview_url,
    COUNT(website_pageview_id)  AS pageviews,
    COUNT(DISTINCT website_session_id) AS unique_sessions
FROM website_pageviews
GROUP BY pageview_url
ORDER BY pageviews DESC;

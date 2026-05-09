-- =============================================================
-- 01_traffic_channel_analysis.sql
-- Maven Fuzzy Factory | Traffic & Marketing Channel Analysis
-- Author: Binh Pham | GitHub: binhpham-2002
-- =============================================================

-- ---------------------------------------------------------------
-- 1. Overall session volume by UTM source & campaign
-- ---------------------------------------------------------------
SELECT
    utm_source,
    utm_campaign,
    COUNT(website_session_id)  AS total_sessions,
    SUM(is_repeat_session)     AS repeat_sessions,
    ROUND(100.0 * SUM(is_repeat_session) / COUNT(website_session_id), 2) AS repeat_rate_pct
FROM website_sessions
GROUP BY utm_source, utm_campaign
ORDER BY total_sessions DESC;


-- ---------------------------------------------------------------
-- 2. Monthly session trend by channel
-- ---------------------------------------------------------------
SELECT
    DATE_FORMAT(created_at, '%Y-%m')  AS yr_month,
    utm_source,
    utm_campaign,
    COUNT(website_session_id)          AS sessions
FROM website_sessions
GROUP BY yr_month, utm_source, utm_campaign
ORDER BY yr_month, sessions DESC;


-- ---------------------------------------------------------------
-- 3. Device-type breakdown per traffic source
-- ---------------------------------------------------------------
SELECT
    utm_source,
    device_type,
    COUNT(website_session_id)                                          AS sessions,
    ROUND(100.0 * COUNT(website_session_id)
          / SUM(COUNT(website_session_id)) OVER (PARTITION BY utm_source), 2) AS pct_of_source
FROM website_sessions
GROUP BY utm_source, device_type
ORDER BY utm_source, sessions DESC;


-- ---------------------------------------------------------------
-- 4. Session-to-order conversion rate by channel
-- ---------------------------------------------------------------
SELECT
    ws.utm_source,
    ws.utm_campaign,
    COUNT(DISTINCT ws.website_session_id)               AS sessions,
    COUNT(DISTINCT o.order_id)                          AS orders,
    ROUND(100.0 * COUNT(DISTINCT o.order_id)
          / COUNT(DISTINCT ws.website_session_id), 2)   AS cvr_pct
FROM website_sessions ws
LEFT JOIN orders o ON ws.website_session_id = o.website_session_id
GROUP BY ws.utm_source, ws.utm_campaign
ORDER BY cvr_pct DESC;


-- ---------------------------------------------------------------
-- 5. New vs. repeat visitor conversion comparison
-- ---------------------------------------------------------------
SELECT
    is_repeat_session,
    COUNT(DISTINCT ws.website_session_id)             AS sessions,
    COUNT(DISTINCT o.order_id)                        AS orders,
    ROUND(100.0 * COUNT(DISTINCT o.order_id)
          / COUNT(DISTINCT ws.website_session_id), 2) AS cvr_pct,
    ROUND(AVG(o.price_usd), 2)                        AS avg_order_value
FROM website_sessions ws
LEFT JOIN orders o ON ws.website_session_id = o.website_session_id
GROUP BY is_repeat_session;


-- ---------------------------------------------------------------
-- 6. Top landing pages by traffic volume (first pageview per session)
-- ---------------------------------------------------------------
SELECT
    pv.pageview_url                     AS landing_page,
    COUNT(DISTINCT pv.website_session_id) AS sessions
FROM website_pageviews pv
INNER JOIN (
    SELECT website_session_id, MIN(website_pageview_id) AS first_pv
    FROM website_pageviews
    GROUP BY website_session_id
) lp ON pv.website_session_id = lp.website_session_id
       AND pv.website_pageview_id = lp.first_pv
GROUP BY landing_page
ORDER BY sessions DESC;


-- cohort_analysis.sql
-- Step 6: Cohort & Retention Analysis
-- Step 7: Customer Segmentation (Frequency / Spend tier / RFM)

-- Cohort analysis: group customers by registration month, then measure
-- how many ordered in month 0 (registration month), month 1, 2, 3,
-- and the retention rate for each month relative to cohort size.
WITH cohorts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort_month
    FROM customers
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers
    FROM cohorts
    GROUP BY cohort_month
),
customer_orders AS (
    SELECT DISTINCT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS order_month
    FROM orders o
    WHERE o.customer_id IS NOT NULL
),
order_month_offset AS (
    SELECT
        co.customer_id,
        c.cohort_month,
        co.order_month,
        -- month offset = difference in months between order_month and cohort_month
        (CAST(strftime('%Y', co.order_month || '-01') AS INTEGER) -
         CAST(strftime('%Y', c.cohort_month || '-01') AS INTEGER)) * 12
        + (CAST(strftime('%m', co.order_month || '-01') AS INTEGER) -
           CAST(strftime('%m', c.cohort_month || '-01') AS INTEGER)) AS month_offset
    FROM customer_orders co
    JOIN cohorts c ON c.customer_id = co.customer_id
),
cohort_activity AS (
    SELECT
        cohort_month,
        month_offset,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM order_month_offset
    WHERE month_offset BETWEEN 0 AND 3
    GROUP BY cohort_month, month_offset
)
SELECT
    cs.cohort_month,
    cs.cohort_customers,
    ca.month_offset,
    ca.active_customers,
    ROUND(100.0 * ca.active_customers / cs.cohort_customers, 2) AS retention_rate_percent
FROM cohort_size cs
JOIN cohort_activity ca ON ca.cohort_month = cs.cohort_month
ORDER BY cs.cohort_month, ca.month_offset;


-- Churned vs repeat customers
--   repeat  = placed 2 or more orders
--   churned = customer's last order was more than 90 days before the most
--             recent order_date in the whole dataset
WITH customer_order_stats AS (
    SELECT
        o.customer_id,
        COUNT(*) AS num_orders,
        MAX(o.order_date) AS last_order_date
    FROM orders o
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM orders
)
SELECT
    cos.customer_id,
    cos.num_orders,
    CASE WHEN cos.num_orders >= 2 THEN 'Repeat' ELSE 'One-time' END AS purchase_type,
    CASE
        WHEN JULIANDAY(dm.max_date) - JULIANDAY(cos.last_order_date) > 90 THEN 'Churned'
        ELSE 'Active'
    END AS churn_status
FROM customer_order_stats cos, dataset_max_date dm
ORDER BY cos.customer_id;


-- Step 7: Customer Segmentation

-- Segment by purchase frequency: one-time / occasional / loyal
WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS num_orders
    FROM orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    customer_id,
    num_orders,
    CASE
        WHEN num_orders = 1 THEN 'One-time'
        WHEN num_orders BETWEEN 2 AND 4 THEN 'Occasional'
        ELSE 'Loyal'
    END AS frequency_segment
FROM order_counts
ORDER BY num_orders DESC;


-- Segment by spend tier: low / medium / high (based on total revenue)

WITH customer_spend AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_spend
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(total_spend, 2) AS total_spend,
    CASE
        WHEN total_spend >= 10000 THEN 'High'
        WHEN total_spend >= 3000 THEN 'Medium'
        ELSE 'Low'
    END AS spend_tier
FROM customer_spend
ORDER BY total_spend DESC;


-- RFM Analysis: Recency, Frequency, Monetary
--   Recency  = days since last order (relative to most recent order in dataset)
--   Frequency = number of orders
--   Monetary  = total revenue
--   Each scored 1-4 via NTILE, combined into an RFM segment

WITH dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM orders
),
rfm_base AS (
    SELECT
        o.customer_id,
        JULIANDAY((SELECT max_date FROM dataset_max_date)) - JULIANDAY(MAX(o.order_date)) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monetary
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        frequency,
        ROUND(monetary, 2) AS monetary,
        -- lower recency_days is better -> ascending order for score 4 = most recent
        NTILE(4) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(4) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(4) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total_score,
    CASE
        WHEN r_score = 1 AND f_score = 1 AND m_score = 1 THEN 'Champion'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Loyal Customer'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'At Risk / Churning'
        ELSE 'Regular'
    END AS rfm_segment
FROM rfm_scored
ORDER BY rfm_total_score;

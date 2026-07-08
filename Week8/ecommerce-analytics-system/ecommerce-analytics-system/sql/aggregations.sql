-- aggregations.sql
-- Basic & Intermediate SQL Analytics: Joins & Aggregations


-- 1. Total revenue per category
--    revenue = quantity * unit_price * (1 - discount_percent/100)
--    (only DELIVERED/positive-quantity items count as "purchase" revenue;
--     returns naturally net out since quantity is negative for them)

SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;


-- 1b. Total revenue per customer, per month  (joins across all 4 tables)

SELECT
    c.customer_id,
    c.customer_name,
    strftime('%Y-%m', o.order_date) AS order_month,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS monthly_revenue
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
GROUP BY c.customer_id, order_month
ORDER BY c.customer_id, order_month;


-- 2. Top 10 customers by total order value
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_type,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_order_value
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
GROUP BY c.customer_id
ORDER BY total_order_value DESC
LIMIT 10;


-- 3. Month-wise order count for the last 12 months
--    (relative to the most recent order_date in the dataset)
WITH latest AS (
    SELECT MAX(order_date) AS max_date FROM orders
)
SELECT
    strftime('%Y-%m', o.order_date) AS order_month,
    COUNT(DISTINCT o.order_id)      AS order_count
FROM orders o, latest
WHERE o.order_date >= datetime(latest.max_date, '-12 months')
GROUP BY order_month
ORDER BY order_month;


-- Top products by quantity sold and revenue
SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id
ORDER BY revenue DESC
LIMIT 20;



-- Average Order Value (AOV) by customer segment (customer_type)
WITH order_values AS (
    SELECT
        o.order_id,
        c.customer_type,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS order_value
    FROM orders o
    JOIN customers c    ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id   = o.order_id
    GROUP BY o.order_id, c.customer_type
)
SELECT
    customer_type,
    COUNT(*)                       AS num_orders,
    ROUND(AVG(order_value), 2)     AS avg_order_value
FROM order_values
GROUP BY customer_type
ORDER BY avg_order_value DESC;



-- 4. Customers who placed orders but never had any item delivered
SELECT c.customer_id, c.customer_name
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id
HAVING SUM(CASE WHEN o.status = 'DELIVERED' THEN 1 ELSE 0 END) = 0;


-- 5. Products that were ordered but had more returns than purchases
--    ("purchases" = rows with positive quantity, "returns" = negative quantity)
SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END)        AS units_purchased,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)       AS units_returned
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id
HAVING units_returned > units_purchased
ORDER BY units_returned DESC;


-- 6. Return rate (returned items / total items) per category
SELECT
    p.category,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_items,
    SUM(ABS(oi.quantity))                                       AS total_items,
    ROUND(
        100.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
        / NULLIF(SUM(ABS(oi.quantity)), 0), 2
    ) AS return_rate_percent
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate_percent DESC;

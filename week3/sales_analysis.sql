-- CREATE DATABASE sales_data;

-- USE sales_data;

-- steps to import database
-- step 1:
--  right-click on the schema 
-- Select Table Data Import Wizard
-- Choose sample_superstore CSV file 

-- step 2: During import:
-- Select Create new table or choose existing table (sample_superstore)
-- Verify column mapping (order_id, order_date, etc.)
-- Keep First row as column headers = ON

-- step 3: Execute Import
-- Click Next
-- Review preview data
-- Click Finish
-- Wait for import completion message

-- Step 4: Verify Imported Data
-- SELECT * FROM sample_superstore LIMIT 10;

-- Creating Normalized Table

-- CREATE TABLE  products (
--     `Product ID` VARCHAR(50) PRIMARY KEY,
--     `Product Name` VARCHAR(255),
--     Category VARCHAR(50),
--     `Sub Category` VARCHAR(50)
-- );

-- CREATE TABLE customers (
--     customer_id INT AUTO_INCREMENT PRIMARY KEY,
--     customer_name VARCHAR(100),
--     segment VARCHAR(50),
--     country VARCHAR(50),
--     city VARCHAR(50),
--     state VARCHAR(50),
--     postal_code VARCHAR(20)
-- );

-- CREATE TABLE orders (
--     order_id VARCHAR(50) PRIMARY KEY,
--     order_date DATE,
--     customer_name VARCHAR(100),
--     product_id VARCHAR(50),
--     sales DECIMAL(10,2),
--     quantity INT,
--     profit DECIMAL(10,2)
-- );

-- Insert commands

-- INSERT INTO customers (customer_name, segment, country, city, state, postal_code)
-- SELECT DISTINCT 
--     customer_name,
--     segment,
--     country,
--     city,
--     state,
--     postal_code
-- FROM sample_superstore;

-- INSERT INTO products
-- SELECT DISTINCT
--     product_id,
--     product_name,
--     category,
--     sub_category
-- FROM superstore_raw;

-- INSERT IGNORE INTO orders
-- SELECT
--     order_id,
--     STR_TO_DATE(order_date, '%m-%d-%Y'),
--     customer_name,
--     product_id,
--     sales,
--     quantity,
--     profit
-- FROM sample_superstore;

-- SELECT COUNT(*) FROM orders;

-- subqueries commands

-- SELECT *
-- FROM orders
-- WHERE sales > (
--     SELECT AVG(sales)
--     FROM orders
-- );


-- SELECT *
-- FROM orders o
-- WHERE sales = (
--     SELECT MAX(sales)
--     FROM orders
--     WHERE customer_name = o.customer_name
-- );


-- SELECT *
-- FROM orders
-- WHERE (customer_name, sales) IN (
--     SELECT customer_name, MAX(sales)
--     FROM orders
--     GROUP BY customer_name
-- );

-- CTE to compute aggregation

WITH customer_sales AS (
    SELECT 
        customer_name,
        SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_name
)
SELECT *
FROM customer_sales;

-- rank customers by sales
-- WITH customer_sales AS (
--     SELECT 
--         customer_name,
--         SUM(sales) AS total_sales
--     FROM orders
--     GROUP BY customer_name
-- )
-- SELECT 
--     customer_name,
--     total_sales,
--     RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
-- FROM customer_sales;


-- WINDOW function for ranking and analysis
-- SELECT
--     order_id,
--     customer_name,
--     sales,
--     ROW_NUMBER() OVER (ORDER BY sales DESC) AS row_num
-- FROM orders;

-- ranking with ties
-- SELECT
--     order_id,
--     customer_name,
--     sales,
--     RANK() OVER (ORDER BY sales DESC) AS sales_rank
-- FROM orders;

-- Using DENSE RANK (NO gaps in ranking)
-- SELECT
--     order_id,
--     customer_name,
--     sales,
--     DENSE_RANK() OVER (ORDER BY sales DESC) AS sales_dense_rank
-- FROM orders;


-- Ranking per Customer
-- SELECT *
-- FROM (
--     SELECT
--         order_id,
--         customer_name,
--         sales,
--         ROW_NUMBER() OVER (
--             PARTITION BY customer_name 
--             ORDER BY sales DESC
--         ) AS rn
--     FROM orders
-- ) t
-- WHERE rn = 1;


--  Top 3 Orders per Customer
-- SELECT *
-- FROM (
--     SELECT
--         order_id,
--         customer_name,
--         sales,
--         RANK() OVER (
--             PARTITION BY customer_name 
--             ORDER BY sales DESC
--         ) AS rnk
--     FROM orders
-- ) t
-- WHERE rnk <= 3;

-- combining JOIN and CTE and WINDOW function s for final result
-- WITH customer_sales AS (
--     SELECT
--         o.customer_name,
--         SUM(o.sales) AS total_sales
--     FROM orders o
--     JOIN customers c
--         ON o.customer_name = c.customer_name
--     GROUP BY o.customer_name
-- ),
-- ranked_customers AS (
--     SELECT
--         customer_name,
--         total_sales,
--         RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
--     FROM customer_sales
-- )
-- SELECT *
-- FROM ranked_customers;


-- solving busisnes queries
-- top customers(by total sales)
-- SELECT
--     customer_name,
--     SUM(sales) AS total_sales
-- FROM orders
-- GROUP BY customer_name
-- ORDER BY total_sales DESC
-- LIMIT 10;


-- low customers(lowest sales contributers)
-- SELECT
--     customer_name,
--     SUM(sales) AS total_sales
-- FROM orders
-- GROUP BY customer_name
-- ORDER BY total_sales ASC
-- LIMIT 10;

-- single order customers
-- SELECT
--     customer_name,
--     COUNT(order_id) AS total_orders
-- FROM orders
-- GROUP BY customer_name
-- HAVING COUNT(order_id) = 1;

-- Customers with Above-Average Sales
-- WITH customer_sales AS (
--     SELECT
--         customer_name,
--         SUM(sales) AS total_sales
--     FROM orders
--     GROUP BY customer_name
-- )
-- SELECT *
-- FROM customer_sales
-- WHERE total_sales > (
--     SELECT AVG(total_sales)
--     FROM customer_sales
-- );


-- WITH customer_sales AS (
--     SELECT
--         customer_name,
--         SUM(sales) AS total_sales
--     FROM orders
--     GROUP BY customer_name
-- )
-- SELECT *
-- FROM customer_sales
-- WHERE total_sales > (
--     SELECT AVG(total_sales)
--     FROM customer_sales
-- );

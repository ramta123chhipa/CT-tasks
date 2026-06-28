/*SECTION - A*/

/*q1.)
SELECT * 
FROM customers;
*/


/*q2.)
SELECT first_name, last_name, city
FROM customers;
*/


/*q3.)
SELECT DISTINCT category
FROM products;
*/

/*q4.)
Primary Keys
customers → customer_id
products → product_id
orders → order_id
order_items → item_id

Why must a Primary Key be UNIQUE?
A primary key uniquely identifies each record in a table. No two rows can have the same 
primary key value. This prevents duplicate records and maintains data integrity.


Why must a Primary Key be NOT NULL?
A primary key cannot contain NULL values because every record must have a valid 
identifier. If a primary key were NULL, the database would not be able to uniquely identify 
that record.
*/



/*q5.)
IN customer table the email has to folow the following constaints:
1.NOT NULL – Every customer must provide an email address.
2.UNIQUE – No two customers can have the same email address.
*/


/*q6.)
INSERT INTO products
(product_id, product_name, category, unit_price)
VALUES
(201, 'Keyboard', 'Electronics', -50);

Result will be an error

The CHECK constraint validates that the product price must be greater than zero. 
Since -50 is a negative value, the database rejects the insertion.
*/




/*SECTION - B*/

/*q7.)
SELECT *
FROM orders
WHERE status = 'Delivered';
*/


/*q8.)
SELECT *
FROM products
WHERE category = 'Electronics'
AND unit_price > 2000;
*/

/*q9.)
SELECT *
FROM customers
WHERE join_date >= '2024-01-01'
AND join_date < '2025-01-01'
AND state = 'Maharashtra';
*/

/*q10.)
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25'
AND status <> 'Cancelled';
*/


/*q11.)
An index is a database object that improves the speed of data retrieval operations.
The index idx_orders_date is created on the order_date column and helps MySQL locate 
rows more efficiently.


How It Improves Performance:-

1.Without an index:
MySQL performs a full table scan.
Every row must be checked.
Query execution becomes slower for large tables.

2.With an index:
MySQL can directly locate matching dates.
Fewer rows are scanned.
Query execution is significantly faster.
CREATE INDEX idx_orders_date
ON orders(order_date);


Query:-
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-08-01' AND '2024-08-31';
*/



/*
q12.)
No, the index on join_date would generally not be used efficiently.

Reason:-
The YEAR() function is applied to every value in the join_date column before comparison.
Since MySQL must calculate the year for each row,
it cannot effectively use the index and may perform a full table scan.


SARGable Query:-
SELECT *
FROM customers
WHERE join_date >= '2024-01-01'
AND join_date < '2025-01-01';
*/



/*SECTION - C*/

/*q13.)
SELECT COUNT(*) AS total_orders
FROM orders;
*/



/*q14.)
SELECT SUM(total_amount) AS total_revenue
FROM orders
WHERE status = 'Delivered';
*/



/*q15.)
SELECT category,
    AVG(unit_price) AS average_price
FROM products
GROUP BY category;
*/



/*q16.)
SELECT status,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_revenue
FROM orders
GROUP BY status
ORDER BY total_revenue DESC;
*/



/*q17.)
SELECT category,
    MAX(unit_price) AS most_expensive_product,
    MIN(unit_price) AS cheapest_product
FROM products
GROUP BY category;
*/



/*q18.)
SELECT category,
    AVG(unit_price) AS average_price
FROM products
GROUP BY category
HAVING AVG(unit_price) > 2000;
*/


/*SECTION - D*/

/*q19.)
SELECT o.order_id,
    o.order_date,
    c.first_name,
    c.last_name,
    o.total_amount
FROM orders o
INNER JOIN customers c
ON o.customer_id = c.customer_id;
*/



/*q20.)
SELECT c.customer_id,
    c.first_name,
    c.last_name,
    o.order_id,
    o.order_date,
    o.total_amount
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id;
*/



/*q21.)
SELECT o.order_id,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    oi.discount_pct
FROM orders o
INNER JOIN order_items oi
ON o.order_id = oi.order_id
INNER JOIN products p
ON oi.product_id = p.product_id;
*/



/*q22.)
The main difference between LEFT and RIGHT JOIN is that
a LEFT JOIN keeps all records fromthe left table (customers),
whereas a RIGHT JOIN keeps all records from the 
right table (orders).

LEFT JOIN:-
SELECT c.customer_id,
    c.first_name,
    c.last_name,
    o.order_id,
    o.status
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id;


RIGHT JOIN:-
SELECT c.customer_id, c.first_name, c.last_name,
    o.order_id, o.status
FROM customers c
RIGHT JOIN orders o
ON c.customer_id = o.customer_id;

A FULL OUTER JOIN is used when we want all records from both tables,
regardless of whether a matching relationship exists. For example,
if we want a complete report showing every customer and every order,
including customers who have never placed an order and orders that 
do not have a matching customer, then a FULL OUTER JOIN would be appropriate.
MySQL does not support FULL OUTER JOIN directly, so it is usually implemented
using a combination of LEFT JOIN and RIGHT JOIN with the UNION operator.
*/



/*q23.)
the Foreign Key relationships are:
1.orders.customer_id references customers.customer_id
2.order_items.order_id references orders.order_id
3.order_items.product_id references products.product_id.

example:
INSERT INTO orders
(order_id, customer_id, order_date, status, total_amount)
VALUES
(1011, 999, '2024-09-01', 'Pending', 2500);

If we try to insert an order with customer_id = 999 and no customer with ID 999
the database will reject the insertion because it violates the Foreign Key constraint.
*/



/*SECTION - E*/

/*q24.)
SELECT product_name,
       unit_price,
       CASE
        WHEN unit_price < 1000 THEN 'Budget'
        WHEN unit_price BETWEEN 1000 AND 3000 THEN 'Mid-Range'
        WHEN unit_price > 3000 THEN 'Premium'
       END AS price_tier
FROM products;
*/



/*q25.)
SELECT
    SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS Delivered_Orders,
    SUM(CASE WHEN status <> 'Delivered' THEN 1 ELSE 0 END) AS Not_Delivered_Orders
FROM orders;
*/



/*q26.)
ACID is a set of properties that ensures database transactions are 
processed reliably and accurately.

Atomicity: Either all operations succeed or none do.
Consistency: Database remains valid before and after a transaction.
Isolation: Simultaneous transactions do not affect each other.
Durability: Committed changes remain saved permanently.

Example: In a bank transfer, money should be deducted and credited together. 
If any step fails, the entire transaction is rolled back.
*/



/*q27.)
START TRANSACTION;

INSERT INTO orders
(order_id, customer_id, order_date, status, total_amount)
VALUES
(1011, 102, CURDATE(), 'Pending', 1598.00);

INSERT INTO order_items
(item_id, order_id, product_id, quantity, unit_price, discount_pct)
VALUES
(5016, 1011, 202, 1, 799.00, 0);

INSERT INTO order_items
(item_id, order_id, product_id, quantity, unit_price, discount_pct)
VALUES
(5017, 1011, 208, 1, 799.00, 0);

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id = 202;

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id = 208;

COMMIT;

/*IF any statement fail:*/
ROLLBACK;

*/
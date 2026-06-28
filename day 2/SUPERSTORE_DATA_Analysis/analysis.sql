-- SELECT * FROM sample_superstore LIMIT 10;

-- SELECT COUNT(*) FROM sample_superstore;

-- DESCRIBE sample_superstore;

-- SELECT *
-- FROM sample_superstore
-- WHERE Category = 'Technology';

-- SELECT * 
-- FROM sample_superstore
-- WHERE Sales > 1000

-- SELECT * 
-- FROM sample_superstore
-- WHERE Region = 'West'

-- SELECT *
-- FROM sample_superstore
-- WHERE STR_TO_DATE(`Order Date`, '%m/%d/%Y')
-- BETWEEN '2016-06-12' AND '2016-07-17';

-- SELECT Category,
-- SUM(Sales) AS Total_Sales
-- FROM sample_superstore
-- GROUP BY Category;

-- SELECT Quantity,
-- COUNT(*) AS Total_Orders
-- FROM sample_superstore
-- GROUP BY Quantity

-- SELECT Region,
-- AVG(Profit) AS Avg_Profit
-- From sample_superstore
-- GROUP BY Region;

-- SELECT `Product Name`,
-- SUM(Sales) AS Total_Sales
-- FROM sample_superstore
-- GROUP BY `Product Name`
-- ORDER BY Total_Sales DESC;

-- SELECT Category,
-- SUM(Profit) AS Total_Profit
-- FROM sample_superstore
-- GROUP BY Category
-- ORDER BY Total_Profit DESC;

-- SELECT MONTH(STR_TO_DATE(`Order Date`, '%m/%d/%Y')) AS Month,
-- SUM(Sales) AS Monthly_Sales
-- FROM sample_superstore
-- GROUP BY MONTH(STR_TO_DATE(`Order Date`, '%m/%d/%Y'))
-- ORDER BY Month;

-- SELECT `Customer Name`,
-- SUM(Sales) AS Total_Purchase
-- FROM sample_superstore
-- GROUP BY `Customer Name`
-- ORDER BY Total_Purchase DESC
-- LIMIT 10;

-- SELECT `Order ID`,
-- COUNT(*) AS Duplicate_Count
-- From sample_superstore
-- GROUP BY `Order ID`
-- HAVING COUNT(*) > 1;

-- SELECT `Sub-Category`,
-- SUM(Profit) AS Total_Profit
-- FROM sample_superstore
-- GROUP BY `Sub-Category`
-- ORDER BY Total_Profit DESC
-- LIMIT 1;

-- SELECT COUNT(*) AS Total_Rows
-- FROM sample_superstore;

-- SELECT *
-- FROM sample_superstore
-- WHERE Sales IS NULL OR Profit IS NULL;

-- SELECT * 
-- FROM sample_superstore
-- WHERE Profit < 0;



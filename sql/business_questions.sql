-- Business questions against olist_star (Hive / Spark SQL)
-- URI: hive://spark-thriftserver:10000/olist_star
--
-- Fact | Dimensions mapping:
-- 1 Monthly revenue              → fact_sales + dim_date
-- 2 Revenue by category          → fact_sales + dim_product
-- 3 Top-performing sellers       → fact_sales + dim_seller
-- 4 Sales by customer state      → fact_sales + dim_customer
-- 5 Avg delivery time by state   → fact_orders + dim_customer
-- 6 Payment method trends        → fact_payments + dim_date
-- 7 Avg review score by category → fact_reviews + fact_sales + dim_product

USE olist_star;

-- 1) Monthly revenue
SELECT
  d.year,
  d.month,
  ROUND(SUM(f.revenue), 2) AS monthly_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 2) Revenue by product category
SELECT
  p.product_category_name_english AS category,
  ROUND(SUM(f.revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_category_name_english
ORDER BY revenue DESC;

-- 3) Top-performing sellers
SELECT
  s.seller_id,
  s.seller_city,
  s.seller_state,
  ROUND(SUM(f.revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_seller s ON f.seller_id = s.seller_id
GROUP BY s.seller_id, s.seller_city, s.seller_state
ORDER BY revenue DESC
LIMIT 20;

-- 4) Sales by customer state
SELECT
  c.customer_state,
  ROUND(SUM(f.revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY revenue DESC;

-- 5) Average delivery time by state
SELECT
  c.customer_state,
  ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
  COUNT(*) AS delivered_orders
FROM fact_orders o
JOIN dim_customer c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.delivery_days IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_delivery_days;

-- 6) Payment method trends (monthly × type)
SELECT
  d.year,
  d.month,
  p.payment_type,
  ROUND(SUM(p.payment_value), 2) AS payment_value
FROM fact_payments p
JOIN dim_date d ON p.date_key = d.date_key
GROUP BY d.year, d.month, p.payment_type
ORDER BY d.year, d.month, p.payment_type;

-- 7) Average review score by category
-- Review is order-level; explode to items to attribute category.
SELECT
  p.product_category_name_english AS category,
  ROUND(AVG(r.review_score), 2) AS avg_review_score,
  COUNT(*) AS review_item_rows
FROM fact_reviews r
JOIN fact_sales f ON r.order_id = f.order_id
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_category_name_english
ORDER BY avg_review_score DESC;

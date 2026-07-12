{{ config(alias='fact_orders') }}
select
  order_id,
  customer_id,
  order_status,
  date_key,
  purchase_date,
  order_purchase_timestamp,
  order_delivered_customer_date,
  order_estimated_delivery_date,
  delivery_days
from {{ ref('silver_orders') }}

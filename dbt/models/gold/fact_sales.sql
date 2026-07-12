{{ config(alias='fact_sales') }}
select
  i.order_id,
  i.order_item_id,
  i.product_id,
  i.seller_id,
  o.customer_id,
  o.date_key,
  o.purchase_date,
  i.price,
  i.freight_value,
  i.revenue
from {{ ref('silver_order_items') }} i
inner join {{ ref('silver_orders') }} o
  on i.order_id = o.order_id

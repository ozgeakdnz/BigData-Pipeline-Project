{{ config(alias='order_items') }}
select
  order_id,
  order_item_id,
  product_id,
  seller_id,
  shipping_limit_date,
  cast(price as double) as price,
  cast(freight_value as double) as freight_value,
  cast(price as double) + cast(freight_value as double) as revenue
from {{ ref('bronze_order_items') }}

{{ config(alias='orders') }}
select
  order_id,
  customer_id,
  order_status,
  order_purchase_timestamp,
  order_approved_at,
  order_delivered_carrier_date,
  order_delivered_customer_date,
  order_estimated_delivery_date,
  to_date(order_purchase_timestamp) as purchase_date,
  cast(date_format(to_date(order_purchase_timestamp), 'yyyyMMdd') as int) as date_key,
  case
    when order_delivered_customer_date is not null
      and order_purchase_timestamp is not null
    then round(
      (unix_timestamp(order_delivered_customer_date) - unix_timestamp(order_purchase_timestamp))
      / 86400.0,
      2
    )
  end as delivery_days
from {{ ref('bronze_orders') }}

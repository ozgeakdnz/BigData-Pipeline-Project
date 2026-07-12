{{ config(alias='fact_payments') }}
select
  p.order_id,
  p.payment_sequential,
  o.date_key,
  o.purchase_date,
  p.payment_type,
  p.payment_installments,
  p.payment_value
from {{ ref('silver_order_payments') }} p
inner join {{ ref('silver_orders') }} o
  on p.order_id = o.order_id

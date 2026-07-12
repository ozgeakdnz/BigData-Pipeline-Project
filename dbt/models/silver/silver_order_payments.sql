{{ config(alias='order_payments') }}
select
  order_id,
  payment_sequential,
  payment_type,
  cast(payment_installments as int) as payment_installments,
  cast(payment_value as double) as payment_value
from {{ ref('bronze_order_payments') }}

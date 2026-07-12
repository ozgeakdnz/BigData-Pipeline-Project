{{ config(alias='fact_reviews') }}
select
  r.review_id,
  r.order_id,
  o.date_key,
  o.purchase_date,
  r.review_score,
  r.review_creation_date
from {{ ref('silver_order_reviews') }} r
left join {{ ref('silver_orders') }} o
  on r.order_id = o.order_id

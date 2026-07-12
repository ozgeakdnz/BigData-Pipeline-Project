{{ config(alias='order_reviews') }}
-- De-duplicate review_id, then keep latest review per order
with deduped as (
  select *
  from (
    select
      *,
      row_number() over (
        partition by review_id
        order by review_answer_timestamp desc nulls last
      ) as rn_review
    from {{ ref('bronze_order_reviews') }}
  ) t
  where rn_review = 1
),
one_per_order as (
  select *
  from (
    select
      *,
      row_number() over (
        partition by order_id
        order by review_answer_timestamp desc nulls last
      ) as rn_order
    from deduped
  ) t
  where rn_order = 1
)
select
  review_id,
  order_id,
  cast(review_score as int) as review_score,
  review_comment_title,
  review_comment_message,
  review_creation_date,
  review_answer_timestamp
from one_per_order

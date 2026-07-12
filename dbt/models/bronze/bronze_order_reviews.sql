{{ config(alias='order_reviews') }}
select * from {{ source('olist_raw', 'order_reviews') }}

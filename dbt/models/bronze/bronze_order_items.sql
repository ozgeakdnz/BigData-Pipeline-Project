{{ config(alias='order_items') }}
select * from {{ source('olist_raw', 'order_items') }}

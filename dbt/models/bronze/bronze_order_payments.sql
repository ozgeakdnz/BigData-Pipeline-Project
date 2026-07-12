{{ config(alias='order_payments') }}
select * from {{ source('olist_raw', 'order_payments') }}

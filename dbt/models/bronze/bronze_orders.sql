{{ config(alias='orders') }}
select * from {{ source('olist_raw', 'orders') }}

{{ config(alias='products') }}
select * from {{ source('olist_raw', 'products') }}

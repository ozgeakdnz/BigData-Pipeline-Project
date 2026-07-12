{{ config(alias='sellers') }}
select * from {{ source('olist_raw', 'sellers') }}

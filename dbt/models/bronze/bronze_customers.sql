{{ config(alias='customers') }}
select * from {{ source('olist_raw', 'customers') }}

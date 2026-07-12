{{ config(alias='geolocation') }}
select * from {{ source('olist_raw', 'geolocation') }}

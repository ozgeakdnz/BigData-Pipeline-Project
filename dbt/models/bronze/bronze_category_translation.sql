{{ config(alias='category_translation') }}
select * from {{ source('olist_raw', 'category_translation') }}

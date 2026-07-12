{{ config(alias='dim_seller') }}
select * from {{ ref('silver_sellers') }}

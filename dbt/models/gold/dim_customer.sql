{{ config(alias='dim_customer') }}
select * from {{ ref('silver_customers') }}

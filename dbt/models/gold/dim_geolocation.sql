{{ config(alias='dim_geolocation') }}
select * from {{ ref('silver_geolocation') }}

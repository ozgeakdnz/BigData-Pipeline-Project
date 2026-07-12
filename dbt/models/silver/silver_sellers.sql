{{ config(alias='sellers') }}
select
  seller_id,
  seller_zip_code_prefix,
  seller_city,
  seller_state
from {{ ref('bronze_sellers') }}

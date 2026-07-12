{{ config(alias='geolocation') }}
-- Full-row de-duplication (~261k duplicate rows in raw)
select distinct
  geolocation_zip_code_prefix,
  geolocation_lat,
  geolocation_lng,
  geolocation_city,
  geolocation_state
from {{ ref('bronze_geolocation') }}

{{ config(alias='products') }}
select
  p.product_id,
  p.product_category_name,
  c.product_category_name_english,
  p.product_name_lenght,
  p.product_description_lenght,
  p.product_photos_qty,
  p.product_weight_g,
  p.product_length_cm,
  p.product_height_cm,
  p.product_width_cm
from {{ ref('bronze_products') }} p
left join {{ ref('bronze_category_translation') }} c
  on p.product_category_name = c.product_category_name

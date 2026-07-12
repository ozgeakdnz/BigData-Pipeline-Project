{{ config(alias='dim_date') }}
select distinct
  date_key,
  purchase_date as date,
  year(purchase_date) as year,
  month(purchase_date) as month,
  date_format(purchase_date, 'MMMM') as month_name,
  quarter(purchase_date) as quarter
from {{ ref('silver_orders') }}
where purchase_date is not null

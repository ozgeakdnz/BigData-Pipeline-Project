# Business Question Answers

Computed from cleaned Olist CSVs using the same grain as the star schema (`fact_sales`, `fact_orders`, `fact_payments`, `fact_reviews` + dimensions).

## 1. Monthly revenue

Fact: `fact_sales` · Dim: `dim_date` (month)

| Month | Revenue (BRL) |
|---|---:|
| 2016-09 | 354.75 |
| 2016-10 | 56,808.84 |
| 2016-12 | 19.62 |
| 2017-01 | 137,188.49 |
| 2017-02 | 286,280.62 |
| 2017-03 | 432,048.59 |
| 2017-04 | 412,422.24 |
| 2017-05 | 586,190.95 |
| 2017-06 | 502,963.04 |
| 2017-07 | 584,971.62 |
| 2017-08 | 668,204.60 |
| 2017-09 | 720,398.91 |
| 2017-10 | 769,312.37 |
| 2017-11 | 1,179,143.77 |
| 2017-12 | 863,547.23 |
| 2018-01 | 1,107,301.89 |
| 2018-02 | 986,908.96 |
| 2018-03 | 1,155,126.82 |
| 2018-04 | 1,159,698.04 |
| 2018-05 | 1,149,781.82 |
| 2018-06 | 1,022,677.11 |
| 2018-07 | 1,058,728.03 |
| 2018-08 | 1,003,308.47 |
| 2018-09 | 166.46 |

**Total revenue:** 15,843,553.24 BRL

## 2. Revenue by product category (Top 10)

Fact: `fact_sales` · Dim: `dim_product`

| Category (EN) | Revenue (BRL) |
|---|---:|
| health_beauty | 1,441,248.07 |
| watches_gifts | 1,305,541.61 |
| bed_bath_table | 1,241,681.72 |
| sports_leisure | 1,156,656.48 |
| computers_accessories | 1,059,272.40 |
| furniture_decor | 902,511.79 |
| housewares | 778,397.77 |
| cool_stuff | 719,329.95 |
| auto | 685,384.32 |
| garden_tools | 584,219.21 |

## 3. Top-performing sellers (Top 10 by revenue)

Fact: `fact_sales` · Dim: `dim_seller`

| Seller ID | City | State | Revenue (BRL) |
|---|---|---|---:|
| `4869f7a5…` | guariba | SP | 249,640.70 |
| `7c67e144…` | itaquaquecetuba | SP | 239,536.44 |
| `53243585…` | lauro de freitas | BA | 235,856.68 |
| `4a3ca931…` | ibitinga | SP | 235,539.96 |
| `fa1c13f2…` | sumare | SP | 204,084.73 |
| `da8622b1…` | piracicaba | SP | 185,192.32 |
| `7e93a43e…` | barueri | SP | 182,754.05 |
| `1025f0e2…` | sao paulo | SP | 172,860.69 |
| `7a67c85e…` | sao paulo | SP | 162,648.38 |
| `955fee92…` | sao paulo | SP | 160,602.68 |

## 4. Sales by customer state

Fact: `fact_sales` · Dim: `dim_customer`

| State | Revenue (BRL) |
|---|---:|
| SP | 5,921,678.12 |
| RJ | 2,129,681.98 |
| MG | 1,856,161.49 |
| RS | 885,826.76 |
| PR | 800,935.44 |
| BA | 611,506.67 |
| SC | 610,213.60 |
| DF | 353,229.44 |
| GO | 347,706.93 |
| ES | 324,801.91 |
| PE | 322,237.69 |
| CE | 275,606.30 |
| PA | 217,647.11 |
| MT | 186,168.96 |
| MA | 151,171.99 |
| PB | 140,987.81 |
| MS | 135,956.67 |
| PI | 108,132.28 |
| RN | 101,895.08 |
| AL | 96,229.40 |
| SE | 73,032.32 |
| TO | 61,354.42 |
| RO | 57,558.02 |
| AM | 27,835.73 |
| AC | 19,669.70 |
| AP | 16,262.80 |
| RR | 10,064.62 |

## 5. Average delivery time by state (delivered orders)

Fact: `fact_orders` · Dim: `dim_customer`

| State | Avg delivery days |
|---|---:|
| SP | 8.76 |
| PR | 11.99 |
| MG | 12.01 |
| DF | 12.97 |
| SC | 14.95 |
| RS | 15.30 |
| RJ | 15.31 |
| GO | 15.61 |
| MS | 15.62 |
| ES | 15.79 |
| TO | 17.66 |
| MT | 18.06 |
| PE | 18.45 |
| RN | 19.28 |
| BA | 19.34 |
| RO | 19.37 |
| PI | 19.46 |
| PB | 20.43 |
| AC | 21.04 |
| CE | 21.27 |
| SE | 21.52 |
| MA | 21.57 |
| PA | 23.77 |
| AL | 24.54 |
| AM | 26.43 |
| AP | 27.19 |
| RR | 29.39 |

## 6. Payment method trends

Fact: `fact_payments` · Dim: `dim_date` + payment_type

### Total by payment type

| Payment type | Total value (BRL) |
|---|---:|
| credit_card | 12,542,084.19 |
| boleto | 2,869,361.27 |
| voucher | 379,436.87 |
| debit_card | 217,989.79 |
| not_defined | 0.00 |

### Monthly × payment type (sample of recent months)

| Month | Payment type | Value (BRL) |
|---|---|---:|
| 2018-05 | boleto | 195,378.93 |
| 2018-05 | credit_card | 927,556.35 |
| 2018-05 | debit_card | 9,710.74 |
| 2018-05 | voucher | 21,336.13 |
| 2018-06 | boleto | 153,350.28 |
| 2018-06 | credit_card | 811,508.56 |
| 2018-06 | debit_card | 35,672.62 |
| 2018-06 | voucher | 23,349.04 |
| 2018-07 | boleto | 198,041.24 |
| 2018-07 | credit_card | 803,674.49 |
| 2018-07 | debit_card | 44,866.18 |
| 2018-07 | voucher | 19,958.84 |
| 2018-08 | boleto | 143,805.90 |
| 2018-08 | credit_card | 797,648.89 |
| 2018-08 | debit_card | 46,001.33 |
| 2018-08 | not_defined | 0.00 |
| 2018-08 | voucher | 34,969.20 |
| 2018-09 | not_defined | 0.00 |
| 2018-09 | voucher | 4,439.54 |
| 2018-10 | voucher | 589.67 |

## 7. Average review score by category (Top 15)

Fact: `fact_reviews` · Dim: `dim_product` (via order_items)

| Category (EN) | Avg review score |
|---|---:|
| cds_dvds_musicals | 4.64 |
| fashion_childrens_clothes | 4.50 |
| books_general_interest | 4.45 |
| costruction_tools_tools | 4.44 |
| flowers | 4.42 |
| books_imported | 4.40 |
| books_technical | 4.36 |
| luggage_accessories | 4.31 |
| food_drink | 4.31 |
| small_appliances_home_oven_and_coffee | 4.30 |
| fashion_shoes | 4.25 |
| food | 4.23 |
| fashion_sport | 4.23 |
| music | 4.21 |
| stationery | 4.20 |

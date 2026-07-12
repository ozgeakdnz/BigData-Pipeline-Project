# Phase 1 Report — Olist Big Data Pipeline

## Özet

Olist Brezilya E-Ticaret veriseti (9 CSV, ~100.000 sipariş) indirildi, Apache Spark ile Parquet formatına dönüştürüldü, HDFS'e yazıldı ve Apache Superset ile görselleştirmeye hazır hale getirildi.

## Pipeline Mimarisi

```
[9 CSV — data/raw/]
        ↓  Spark (analysis.py)
[HDFS Parquet — hdfs://namenode:9000/olist/]
        ↓  Hive ThriftServer (port 10000)
[Apache Superset — grafikler]
```

## Veri Seti

| Tablo | Satır | Açıklama |
|---|---|---|
| orders | 99.441 | Sipariş yaşam döngüsü |
| customers | 99.441 | Müşteri profilleri |
| order_items | 112.650 | Sipariş kalemleri |
| order_payments | 103.886 | Ödeme yöntemleri |
| order_reviews | 104.162 | Müşteri yorumları |
| products | 32.951 | Ürün kataloğu |
| sellers | 3.095 | Satıcı profilleri |
| geolocation | 1.000.163 | Posta kodu → koordinat |
| category_translation | 71 | Kategori çevirisi (PT→EN) |

**Kaynak:** [Kaggle — Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

## Uygulama Adımları

### 1. Veri İndirme (kagglehub)

```bash
python scripts/download_dataset.py
```

### 2. Altyapı Başlatma

```bash
bash scripts/setup_network.sh
docker compose -f docker/docker-compose-hdfs.yml up -d
docker compose -f docker/docker-compose-spark.yml up -d
docker compose -f docker/docker-compose-superset.yml up -d
```

### 3. CSV → Parquet Dönüşümü

```bash
docker exec -e CSV_DIR=/app/data/raw spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /app/processing/analysis.py
```

### 4. Hive Tablo Kaydı

```bash
python visualization/register_tables.py
```

### 5. Superset Bağlantısı

1. http://localhost:8088 → `admin` / `admin`
2. **Settings → Database Connections → + Database**
3. **Hive** seçin
4. SQLAlchemy URI:

```
hive://spark-thriftserver:10000/olist
```

5. **Test Connection** → **Connect**

## Önerilen Grafikler

Superset'te aşağıdaki basit chart'ları oluşturabilirsiniz:

| Grafik | Tablo | Metrik / Boyut |
|---|---|---|
| Aylık sipariş sayısı | `orders` | COUNT(order_id) × order_purchase_timestamp (ay) |
| Ödeme türü dağılımı | `order_payments` | SUM(payment_value) × payment_type |
| Eyalet bazlı müşteri sayısı | `customers` | COUNT(customer_id) × customer_state |
| Ortalama review skoru | `order_reviews` | AVG(review_score) |
| En çok satan kategoriler | `order_items` + `products` | COUNT × product_category_name |

## Servis URL'leri

| Servis | URL | Kimlik |
|---|---|---|
| HDFS NameNode | http://localhost:9870 | — |
| Spark Master | http://localhost:8080 | — |
| Spark ThriftServer | localhost:10000 | — |
| Superset | http://localhost:8088 | admin / admin |

## Tek Komutla Çalıştırma

```bash
bash scripts/run_pipeline.sh
```

## Durdurma

```bash
docker compose -f docker/docker-compose-superset.yml down
docker compose -f docker/docker-compose-spark.yml down
docker compose -f docker/docker-compose-hdfs.yml down
```

---

# Building Data Pipeline — STUDY

Goal (business view): turn **raw data** into **actionable information** via a
**unidirectional** pipeline (source → storage → transform → answers/charts).

A robust pipeline should be:

| Attribute | How we meet it |
|---|---|
| **Clearly defined expectations** | 7 business questions → fixed fact/dim mapping + documented metrics (`revenue = price + freight`) |
| **Scalable architecture** | Spark + HDFS Parquet; add workers/nodes without changing model logic |
| **Reproducible and clear** | Scripts in repo (`download` → `analysis` → `build_star_schema` → SQL/Python answers); one-command `scripts/run_pipeline.sh` |

Deliverables for this STUDY:

| Artifact | Path |
|---|---|
| Data quality + dedupe proof | `reports/data_quality.md` |
| Star schema builder (Spark) | `processing/build_star_schema.py` |
| Business answers (Python) | `processing/business_questions.py` → `reports/business_answers.md` |
| Business answers (SQL) | `sql/business_questions.sql` |
| This write-up | `reports/REPORT.md` (this section) |

## 1. Is data clean? What does clean mean? Duplicates?

**Clean data** = fit for the questions we ask: known grain, no accidental duplicate
entities, nulls handled explicitly, consistent types, measures defined once.

**Findings (see `reports/data_quality.md` for full numbers):**

- Core keys (`order_id`, item PK, payment PK, `customer_id`, `seller_id`, `product_id`) are unique → **clean**.
- `customer_unique_id` repeats = same person, multiple orders → **not a bug**, keep.
- **`geolocation`**: ~261k full-row duplicates → **de-duplicated** in `build_star_schema.py`.
- **`order_reviews`**: duplicate `review_id` (~814) → **de-duplicated**; multiple reviews per order → keep **latest** for order-level KPIs.
- Delivery timestamp nulls (~3%) → excluded from delivery-time averages.
- Review comment nulls are common → OK for score-based KPIs.

**Verdict:** Not fully clean out of the box. We **do de-duplicate** geolocation and reviews before analytics.

## 2. What should output look like? (reasoning)

Input is **normalized operational CSVs** (OLTP-style). Business questions need
**aggregations by attributes** (month, category, seller, state, payment type).

So the output must be an **analytical star schema**:

- **Fact tables** hold numeric measures at a clear grain.
- **Dimension tables** hold descriptive attributes used to slice facts.

| Business Question | Fact Table | Dimensions |
|---|---|---|
| Monthly revenue | `fact_sales` | `dim_date` |
| Revenue by product category | `fact_sales` | `dim_product` |
| Top-performing sellers | `fact_sales` | `dim_seller` |
| Sales by customer state | `fact_sales` | `dim_customer` |
| Average delivery time by state | `fact_orders` | `dim_customer` |
| Payment method trends | `fact_payments` | `dim_date` (+ `payment_type`) |
| Average review score by category | `fact_reviews` | `dim_product` (via `fact_sales` / order items) |

Grain:

- `fact_sales` → 1 row per **order item** (revenue)
- `fact_orders` → 1 row per **order** (delivery_days)
- `fact_payments` → 1 row per **payment line**
- `fact_reviews` → 1 row per **order review** (deduped)

Computed answers: `reports/business_answers.md`  
Executable SQL: `sql/business_questions.sql`

## 3. ETL or ELT? Why? What is dbt?

### Approach: **ELT**

1. **E/L** — Extract CSVs, load as raw Parquet to HDFS (`processing/analysis.py`) with little business logic.  
2. **T** — Transform on the lake: clean + build star (`processing/build_star_schema.py`).

**Why not ETL?** Cleaning before load would force re-ingest for every modeling change. ELT keeps a reusable bronze layer and lets us iterate transforms (and answer new questions) without re-downloading CSVs.

**Why not only SQL Lab ad-hoc?** Reproducibility — transforms live in versioned code and write durable Parquet facts/dims.

### dbt (data build tool)

[dbt](https://www.getdbt.com/) is a **SQL-first transformation framework** that runs *after* data is loaded into a warehouse/lakehouse:

- Each model is a `.sql` (or Python) file; `ref('dim_customer')` builds a DAG.
- Materializations: view / table / incremental.
- Built-in **tests** (`unique`, `not_null`, relationships), docs, and lineage.
- Fits **ELT**: warehouse does the heavy transform; dbt orchestrates SQL.

**In this project** Spark Python plays the same role as dbt models (build dims/facts, dedupe). A production evolution would be: raw Parquet in HDFS/S3 → dbt-spark or dbt on Snowflake/BigQuery → same star schema → BI.

## 4. Layers / architecture logic

Unidirectional flow (source → storage → curated analytics → consumption):

```
[9 Olist CSVs]
      │  download_dataset.py
      ▼
[data/raw] ──────────────────────────── local landing
      │  Spark analysis.py
      ▼
[HDFS /olist/{table}] ──────────────── bronze (raw Parquet)
      │  Spark build_star_schema.py
      │  (dedupe geo/reviews, build facts/dims)
      ▼
[HDFS /olist/star/] ─────────────────── gold (star schema)
      │  Hive ThriftServer (olist_star)
      ├──────────────────► Superset charts
      └──────────────────► SQL + Python business answers
```

Logic: raw stays queryable; analytics only trust **star** tables; one-way dependencies keep the pipeline clear and reproducible.

## 5. Star schema — facts, dimensions, how questions are answered

```
                 dim_date
                    │
   dim_customer ─ fact_sales ─ dim_product
                    │
               dim_seller

   dim_customer ─ fact_orders
   dim_date     ─ fact_payments
   dim_date     ─ fact_reviews ── order_id ── fact_sales ── dim_product
```

| Table | Kind | Role |
|---|---|---|
| `dim_date` | Dimension | year, month, quarter from purchase date |
| `dim_customer` | Dimension | city / **state** |
| `dim_seller` | Dimension | seller city / state |
| `dim_product` | Dimension | category PT + **EN** |
| `dim_geolocation` | Dimension | deduped zip → lat/lng |
| `fact_sales` | Fact | `price`, `freight_value`, `revenue` |
| `fact_orders` | Fact | `delivery_days`, status |
| `fact_payments` | Fact | `payment_type`, `payment_value` |
| `fact_reviews` | Fact | `review_score` |

**How a question is answered:** pick the fact → join dimensions in the mapping table (§2) → `SUM`/`AVG`/`ORDER BY`.  
Example — *sales by customer state*:

```sql
SELECT c.customer_state, SUM(f.revenue) AS revenue
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_state;
```

### Run everything

```bash
python3 processing/data_quality.py
python3 processing/business_questions.py

docker exec spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /app/processing/build_star_schema.py

python3 visualization/register_tables.py
# Then run statements in sql/business_questions.sql via beeline / SQL Lab
```

Superset URI (star): `hive://spark-thriftserver:10000/olist_star`

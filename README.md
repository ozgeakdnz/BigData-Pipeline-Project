# Big Data Analytics Pipeline — Olist E-Commerce

A hands-on big data project built around the
[Olist Brazilian E-Commerce public dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) —
~100,000 real orders from Brazil's largest online marketplace (2016–2018).

The pipeline is developed in **three phases**. Each phase adds orchestration, modeling, and analytics capability on top of the previous one.

| Phase | Focus | Status |
|---|---|---|
| **Phase 1** | Ingest CSV → Spark → HDFS Parquet → Superset charts | ✅ Done |
| **Phase 2** | Data quality, ELT star schema, business KPIs | ✅ Done |
| **Phase 3** | Airflow orchestration + dbt Medallion (Bronze / Silver / Gold) | ✅ Done |

---

## 📌 Submission

Fork this repository, implement your solution, and submit by opening a **Pull Request** back to the upstream repository. PRs are the only accepted submission method.

Docker Compose files in this repo are a **reference setup**. You may run HDFS, Spark, Superset, and Airflow however you prefer, as long as the pipeline works end-to-end.

---

## Dataset

Nine CSV tables from Kaggle (~100k orders):

| File | ~Rows | Description |
|---|---:|---|
| `olist_orders_dataset.csv` | 100k | Order lifecycle, timestamps, status |
| `olist_order_items_dataset.csv` | 112k | Product, seller, price, freight |
| `olist_order_payments_dataset.csv` | 104k | Payment type, installments, value |
| `olist_order_reviews_dataset.csv` | 100k | Review score (1–5), comments |
| `olist_customers_dataset.csv` | 100k | Customer city, state, zip |
| `olist_sellers_dataset.csv` | 3k | Seller city, state, zip |
| `olist_products_dataset.csv` | 33k | Category, dimensions, weight |
| `olist_geolocation_dataset.csv` | 1M | ZIP code → lat/lng |
| `product_category_name_translation.csv` | 71 | Portuguese → English category names |

Download:

```bash
python scripts/download_dataset.py
```

Files land in `data/raw/` (gitignored).

---

## End-to-end architecture

```
                         ┌─────────────────────────────────────────┐
                         │           Phase 3 — Airflow DAG          │
                         │  download → Spark ingest → Hive reg    │
                         │           → dbt run → dbt test           │
                         └────────────────────┬────────────────────┘
                                              │
[9 CSV files]                                 ▼
     │                              ┌─────────────────┐
     │  Spark (analysis.py)         │  Apache Airflow  │  :8089
     ▼                              └─────────────────┘
[HDFS /olist/]  ← Bronze landing (raw Parquet)
     │
     │  dbt Bronze → Silver → Gold
     ▼
┌────────────┬────────────┬────────────┐
│  bronze    │   silver   │    gold    │
│  (raw 1:1) │  (cleaned) │ (star dim/ │
│            │            │   fact)    │
└────────────┴────────────┴────────────┘
     │                              │
     ▼                              ▼
[Hive ThriftServer :10000]    [Superset :8088]
     │                              │
     └────────── BI / SQL KPIs ──────┘
```

**Tech stack:** Apache Spark · HDFS · Hive ThriftServer · Apache Superset · Apache Airflow · dbt-spark

---

## Phase 1 — Ingest & Visualize

**Goal:** Download the dataset, load CSVs into HDFS as Parquet via Spark, connect Superset, and build simple charts.

### What we built

| Component | Path | Role |
|---|---|---|
| Dataset download | `scripts/download_dataset.py` | Kaggle → `data/raw/` via kagglehub |
| Spark ingest | `processing/analysis.py` | CSV → Parquet on `hdfs://namenode:9000/olist/` |
| Hive registration | `visualization/register_tables.py` | Register raw tables in Hive schema `olist` |
| One-command run | `scripts/run_pipeline.sh` | Full Phase 1 stack end-to-end |

### Superset connection

1. Open http://localhost:8088 → `admin` / `admin`
2. **Settings → Database Connections → + Database → Hive**
3. URI: `hive://spark-thriftserver:10000/olist`
4. Create datasets via **SQL Lab** (e.g. `SELECT * FROM olist.orders LIMIT 1000` → Save dataset)

> **Note:** Superset may list table names incorrectly for Spark Hive (`olist` instead of `orders`). Use SQL Lab with fully qualified names (`olist.orders`).

### Charts created

| Chart | Dataset | Metric × Dimension |
|---|---|---|
| Monthly orders | `orders` | COUNT(order_id) × order_purchase_timestamp (month) |
| Payment type distribution | `order_payments` | SUM/COUNT × payment_type |
| Customers by state | `customers` | COUNT(customer_id) × customer_state |
| Average review score | `order_reviews` | AVG(review_score) |

### Screenshots (Phase 1 — Superset)

**Monthly orders**

![Monthly orders](reports/screenshots/monthly-orders-2026-07-12T22-46-47.184Z.jpg)

**Payment type distribution**

![Payment type distribution](reports/screenshots/payment-type-distribution-2026-07-12T22-46-50.967Z.jpg)

**Customers by state**

![Customers by state](reports/screenshots/customers-by-state-2026-07-12T22-46-44.234Z.jpg)

**Average review score**

![Average review score](reports/screenshots/average-review-score-2026-07-12T22-46-41.032Z.jpg)

### Run Phase 1

```bash
bash scripts/setup_network.sh
docker compose -f docker/docker-compose-hdfs.yml up -d
docker compose -f docker/docker-compose-spark.yml up -d
docker compose -f docker/docker-compose-superset.yml up -d

docker exec -e CSV_DIR=/app/data/raw spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /app/processing/analysis.py

python visualization/register_tables.py
```

Or: `bash scripts/run_pipeline.sh`

---

## Phase 2 — Building Data Pipeline (STUDY)

**Goal:** Assess data quality, deduplicate dirty tables, build a star schema (ELT), and answer seven business questions with Python and SQL.

Full write-up: [`reports/REPORT.md`](reports/REPORT.md) (STUDY section)

### Data quality & deduplication

| Finding | Action |
|---|---|
| Core PKs (orders, items, payments, customers…) unique | Keep as-is |
| `geolocation` ~261k full-row duplicates | `dropDuplicates()` |
| `order_reviews` ~814 duplicate `review_id` | Dedupe by `review_id`; one review per order |
| Null delivery timestamps (~3%) | Exclude from delivery-time KPIs |

Reports: [`reports/data_quality.md`](reports/data_quality.md) · Script: `processing/data_quality.py`

### ELT approach

1. **Extract / Load** — CSV → Spark → raw Parquet on HDFS (`processing/analysis.py`)
2. **Transform** — Clean + star schema on HDFS (`processing/build_star_schema.py`)

Why **ELT:** raw data stays reproducible; transforms are iterative and versioned in code.

### Star schema (Spark — `olist_star`)

```
                 dim_date
                    │
   dim_customer ─ fact_sales ─ dim_product
                    │
               dim_seller

   dim_customer ─ fact_orders
   dim_date     ─ fact_payments
   dim_date     ─ fact_reviews
```

| Layer | Hive schema | Tables |
|---|---|---|
| Raw | `olist` | 9 source tables |
| Star | `olist_star` | 5 dims + 4 facts |

### Business questions answered

| Question | Fact | Dimensions |
|---|---|---|
| Monthly revenue | `fact_sales` | `dim_date` |
| Revenue by product category | `fact_sales` | `dim_product` |
| Top-performing sellers | `fact_sales` | `dim_seller` |
| Sales by customer state | `fact_sales` | `dim_customer` |
| Average delivery time by state | `fact_orders` | `dim_customer` |
| Payment method trends | `fact_payments` | `dim_date` + payment_type |
| Average review score by category | `fact_reviews` | `dim_product` |

Answers: [`reports/business_answers.md`](reports/business_answers.md)  
SQL: [`sql/business_questions.sql`](sql/business_questions.sql)  
Python: `processing/business_questions.py`

Example result: **total revenue ~15.8M BRL**; top state **SP**; top category **health_beauty**.

### Run Phase 2 transforms

```bash
docker exec spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /app/processing/build_star_schema.py

python processing/data_quality.py
python processing/business_questions.py
python visualization/register_tables.py
```

Superset (star layer): `hive://spark-thriftserver:10000/olist_star`

---

## Phase 3 — Re-Construct: Airflow + dbt Medallion

**Goal:** Orchestrate the pipeline with **Apache Airflow** and rebuild the star schema as a **dbt** project using **Medallion Architecture** (Bronze → Silver → Gold).

Full STUDY write-up: [`reports/PHASE3.md`](reports/PHASE3.md)

### Airflow DAG — `olist_medallion_pipeline`

```
download_dataset
       ↓
spark_ingest_bronze        ← Spark: CSV → HDFS Parquet
       ↓
register_raw_hive_tables   ← Hive schema `olist`
       ↓
dbt_run_medallion          ← Bronze / Silver / Gold models
       ↓
dbt_test                   ← unique, not_null tests on gold
```

| Task | Operator | Boundary |
|---|---|---|
| `download_dataset` | BashOperator | Host scripts / mounted volume |
| `spark_ingest_bronze` | BashOperator → `docker exec spark-submit` | Spark cluster |
| `register_raw_hive_tables` | BashOperator → Python | Hive ThriftServer |
| `dbt_run_medallion` | BashOperator → `dbt run` | Thrift SQL warehouse |
| `dbt_test` | BashOperator → `dbt test` | Thrift SQL warehouse |

Schedule: `@daily` · UI: http://localhost:8089 (`admin` / `admin`)

### dbt Medallion layers

| Layer | Hive schema | Purpose | Example models |
|---|---|---|---|
| **Bronze** | `bronze` | 1:1 copy of raw sources | `bronze_orders`, `bronze_geolocation` |
| **Silver** | `silver` | Clean, typed, deduped | `silver_orders` (delivery_days), `silver_geolocation` (distinct), `silver_order_reviews` (deduped) |
| **Gold** | `gold` | Star schema for BI | `dim_*`, `fact_sales`, `fact_orders`, `fact_payments`, `fact_reviews` |

dbt project: `dbt/` · DAG: `airflow/dags/olist_medallion_dag.py`

Superset (gold layer): `hive://spark-thriftserver:10000/gold`

### Screenshot (Phase 3 — Airflow DAG graph)

![Airflow olist_medallion_pipeline DAG](reports/screenshots/airflow-olist-medallion-graph.png)

### Run Phase 3

```bash
bash scripts/run_phase3.sh
# Open http://localhost:8089 → trigger DAG: olist_medallion_pipeline
```

Manual dbt (after ingest):

```bash
docker exec -e DBT_SPARK_HOST=spark-thriftserver airflow-scheduler \
  bash -c 'cd /opt/airflow/dbt && dbt run --profiles-dir /opt/airflow/dbt && dbt test --profiles-dir /opt/airflow/dbt'
```

---

## Service URLs

| Service | URL | Credentials |
|---|---|---|
| HDFS NameNode | http://localhost:9870 | — |
| Spark Master | http://localhost:8080 | — |
| Spark ThriftServer | localhost:10000 | — |
| Superset | http://localhost:8088 | admin / admin |
| Airflow | http://localhost:8089 | admin / admin |

---

## Project structure

```
BigData-Pipeline-Project/
├── airflow/
│   └── dags/olist_medallion_dag.py    # Phase 3 orchestration
├── dbt/
│   └── models/
│       ├── bronze/                     # Raw 1:1 models
│       ├── silver/                     # Cleaned / typed
│       └── gold/                       # Star schema (dim + fact)
├── docker/
│   ├── docker-compose-hdfs.yml
│   ├── docker-compose-spark.yml
│   ├── docker-compose-superset.yml
│   └── docker-compose-airflow.yml      # Phase 3
├── processing/
│   ├── analysis.py                     # Phase 1: CSV → Parquet
│   ├── build_star_schema.py            # Phase 2: Spark star schema
│   ├── data_quality.py                 # Phase 2: quality report
│   └── business_questions.py           # Phase 2: KPI answers
├── scripts/
│   ├── download_dataset.py
│   ├── run_pipeline.sh                 # Phase 1 + 2 end-to-end
│   └── run_phase3.sh                   # Phase 3 stack
├── sql/business_questions.sql          # Phase 2 KPI SQL
├── visualization/register_tables.py    # Hive table registration
└── reports/
    ├── REPORT.md                       # Phase 1 + Phase 2 STUDY
    ├── PHASE3.md                       # Phase 3 STUDY
    ├── data_quality.md
    ├── business_answers.md
    └── screenshots/                    # Superset + Airflow captures
```

---

## Reports & deliverables

| Document | Content |
|---|---|
| [`reports/REPORT.md`](reports/REPORT.md) | Phase 1 steps + Phase 2 STUDY (clean data, ELT, dbt intro, layers, star schema) |
| [`reports/PHASE3.md`](reports/PHASE3.md) | Phase 3 STUDY (Airflow components, DAG walk-through, Medallion, challenges) |
| [`reports/data_quality.md`](reports/data_quality.md) | Duplicate analysis and dedupe proof |
| [`reports/business_answers.md`](reports/business_answers.md) | Seven business question results |
| [`reports/screenshots/`](reports/screenshots/) | Superset charts + Airflow DAG graph |

---

## Stop all services

```bash
docker compose -f docker/docker-compose-airflow.yml down
docker compose -f docker/docker-compose-superset.yml down
docker compose -f docker/docker-compose-spark.yml down
docker compose -f docker/docker-compose-hdfs.yml down
```

---

## Author

Implemented as part of the Big Data Analytics Pipeline course — Olist E-Commerce project (Phases 1–3).

# Phase 3 — Re-Construct The Data Pipeline

## Objectives

1. **Apache Airflow** orchestrates ingest + transform (schedule, monitor, retry).
2. **dbt** rebuilds the star schema as a **Medallion** pipeline (Bronze → Silver → Gold).

---

## 1. Apache Airflow core components (1 sentence each)

| Component | One-sentence explanation |
|---|---|
| **Scheduler** | Continuously parses DAGs and triggers task instances when their dependencies and schedule are met. |
| **Executor** | Determines *how* tasks run (here **LocalExecutor** — processes on the scheduler/worker host). |
| **Webserver** | Provides the UI to inspect DAGs, logs, task duration, and manually trigger runs (`http://localhost:8089`). |
| **Metadata DB** | Postgres store for DAG/task state, connections, and variables (`airflow-db`). |
| **DAG** | A versioned Python workflow graph defining tasks and their dependencies. |
| **Operator** | A task template (we use **BashOperator** to call Dockerized Spark and dbt CLI). |
| **Worker** | Process that actually executes task code (LocalExecutor spawns local processes). |

---

## 2. Airflow DAG walk-through

**DAG id:** `olist_medallion_pipeline`  
**File:** `airflow/dags/olist_medallion_dag.py`  
**Schedule:** `@daily` · **catchup:** false · **max_active_runs:** 1

```
download_dataset
       ↓
spark_ingest_bronze     ← Spark cluster (CSV → HDFS Parquet)
       ↓
register_raw_hive_tables
       ↓
dbt_run_medallion       ← Bronze / Silver / Gold models
       ↓
dbt_test
```

### Architectural decisions

| Decision | Why |
|---|---|
| Keep Spark for CSV→Parquet ingest | Matches Phase 1; large files belong on the Spark/HDFS cluster, not inside the Airflow container |
| dbt for Silver/Gold transforms | PDF requires migrating the star schema to dbt; SQL models are testable and modular |
| BashOperator + `docker exec` | Explicit boundary: Airflow orchestrates, Spark executes; no Spark jars inside Airflow image |
| LocalExecutor | Simple, reproducible for coursework; no Celery/Redis ops overhead |
| Airflow on port **8089** | Avoid clash with Spark Master UI on 8080 |
| `retries=1`, `execution_timeout` per task | Clear failure bounds; long Spark/dbt jobs don’t hang forever |
| `max_active_runs=1` | Prevent overlapping Spark jobs contending for the same cluster |

### Task boundaries, operators, resources

| Task | Boundary | Operator | Resources / config |
|---|---|---|---|
| `download_dataset` | Project host scripts / mounted volume | BashOperator | Light CPU; timeout via DAG default 45m |
| `spark_ingest_bronze` | Spark cluster (`spark-master` + worker 4g/2 cores) | BashOperator → `docker exec` + `spark-submit` | `spark.executor.memory=2g`, `driver=1g`, task timeout 30m |
| `register_raw_hive_tables` | Hive ThriftServer metastore | BashOperator → Python | Timeout 10m |
| `dbt_run_medallion` | Thrift SQL warehouse (`spark-thriftserver:10000`) | BashOperator → `dbt run` | Profile `spark.driver.memory=2g`, timeout 40m |
| `dbt_test` | Same Thrift warehouse | BashOperator → `dbt test` | Timeout 15m |

---

## 3. dbt Medallion Architecture

Star schema logic formerly in `processing/build_star_schema.py` is rebuilt as dbt models under `dbt/models/`.

### Diagram

```
                    ┌─────────────────────────┐
                    │  CSV (data/raw)         │
                    └───────────┬─────────────┘
                                │ Spark ingest (Airflow)
                                ▼
┌──────────────────────────────────────────────────────────┐
│ BRONZE  (schema: bronze)                                  │
│  1:1 copy of raw Hive sources — immutable landing         │
│  bronze_orders, bronze_order_items, … bronze_geolocation  │
└───────────────────────────┬──────────────────────────────┘
                            │ dbt (clean / type / enrich)
                            ▼
┌──────────────────────────────────────────────────────────┐
│ SILVER  (schema: silver)                                  │
│  Deduped geo & reviews, typed measures, delivery_days     │
│  silver_orders, silver_order_reviews, silver_geolocation… │
└───────────────────────────┬──────────────────────────────┘
                            │ dbt (star schema)
                            ▼
┌──────────────────────────────────────────────────────────┐
│ GOLD  (schema: gold)                                      │
│  dim_customer, dim_seller, dim_product, dim_date,         │
│  dim_geolocation, fact_sales, fact_orders,                │
│  fact_payments, fact_reviews                              │
└───────────────────────────┬──────────────────────────────┘
                            │
              Superset / SQL business questions
```

### Layer benefits

| Layer | Benefit |
|---|---|
| **Bronze** | Reproducible raw snapshot; re-run Silver/Gold without re-ingesting CSVs |
| **Silver** | Single place for quality rules (dedupe, casts); prevents dirty joins in BI |
| **Gold** | Business-friendly star; stable contracts for Superset and KPI SQL |
| **Separation** | Teams can change Gold models without touching Bronze landing |

### How to run dbt manually

```bash
# From Airflow container or a host with dbt-spark + network access to thriftserver:
cd dbt
DBT_SPARK_HOST=spark-thriftserver dbt run --profiles-dir .
DBT_SPARK_HOST=spark-thriftserver dbt test --profiles-dir .

# From host machine (Thrift port published):
DBT_SPARK_HOST=localhost dbt run --profiles-dir .
```

Superset can point at Gold:

```
hive://spark-thriftserver:10000/gold
```

---

## 4. Challenging parts of this reconstruction

1. **Two compute planes** — Airflow does not run Spark jobs natively; bridging via `docker exec` / socket mount adds ops complexity (permissions, path mounts).
2. **dbt-spark + ThriftServer** — Spark Thrift SQL dialect and metastore quirks (schema naming, `NULL` ordering, parquet table creates) differ from Snowflake/BigQuery dbt docs.
3. **Migrating Python star logic to SQL** — Window functions for review dedupe and date_key derivation had to be re-expressed carefully in Spark SQL.
4. **Idempotency & ordering** — Ingest must finish and Hive tables must exist before `dbt run`; DAG dependencies encode that, but partial failures need clear retries/timeouts.
5. **Port / resource collisions** — Spark UI (8080) vs Airflow (8089); worker memory must leave headroom for ThriftServer + dbt sessions.
6. **LocalExecutor limits** — Fine for class projects; production would need Celery/Kubernetes executors and proper secrets management (Fernet key, no default admin password).

---

## Quick start (Phase 3)

```bash
bash scripts/setup_network.sh
docker compose -f docker/docker-compose-hdfs.yml up -d
docker compose -f docker/docker-compose-spark.yml up -d
# Creates .env with Fernet key if missing, then starts Airflow
bash scripts/run_phase3.sh
# or: docker compose --env-file .env -f docker/docker-compose-airflow.yml up -d --build
```

Open Airflow → trigger DAG **`olist_medallion_pipeline`**.

| Service | URL | Login |
|---|---|---|
| Airflow | http://localhost:8089 | admin / admin |
| Spark | http://localhost:8080 | — |
| HDFS | http://localhost:9870 | — |

# Big Data Analytics Pipeline — Olist E-Commerce

A hands-on big data project built around the
[Olist Brazilian E-Commerce public dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) —
~100,000 real orders from Brazil's largest online marketplace (2016–2018).

The project is developed in stages. Each stage adds a new layer to the pipeline. More stages will be added over time.

---

## 📌 Important Notes

### Submission
Each student must **fork or clone this repository**, implement their solution, and submit by **opening a Pull Request (PR) back to this repository** with their completed work. PRs are the only accepted submission method.

### Docker is Optional
The Docker Compose files and scripts provided in this repo are **starter code only** — a reference setup to help you get up and running quickly. You are **not required** to use Docker. Feel free to run HDFS, Spark, and Superset however you prefer (local install, cloud, a different container setup, etc.), as long as the pipeline works end-to-end.

---

## Architecture (Phase 1)

```
[Olist Dataset — 9 CSV Tables]
        |
        v
[Apache Spark]
  · Reads CSVs
  · Writes Parquet
        |
        v
[HDFS or MinIO]
        |
        v
[Apache Superset — Simple Charts]
```

---


## Phases

### ✅ Phase 1 — Ingest & Visualize

> **Current task**

- Download the Olist dataset (9 CSV tables).
- Import all CSVs into **HDFS or MinIO** in **Parquet format** using Apache Spark.
- Connect Apache Superset to the stored data and create a few simple charts/diagrams.

No advanced transformations are required for this phase.

---

### ✅ Phase 2 — Clean, star schema, business questions

Data quality, ELT star schema, and KPI answers — see `reports/REPORT.md` STUDY section.

### ✅ Phase 3 — Airflow + dbt Medallion

Orchestrate ingest with **Apache Airflow** and rebuild transforms as a **dbt** Medallion project (Bronze / Silver / Gold). See `reports/PHASE3.md`.

---

## Docker Quick Start (Optional)

The following commands use the provided Docker Compose files as a starting point.

**1. Create the shared network**

```bash
# Linux / macOS
bash scripts/setup_network.sh

# Windows (PowerShell)
.\scripts\setup_network.ps1
```

**2. Start the services**

```bash
docker compose -f docker/docker-compose-hdfs.yml up -d
docker compose -f docker/docker-compose-spark.yml up -d
docker compose -f docker/docker-compose-superset.yml up -d
```

| Service         | URL                       | Credentials   |
|-----------------|---------------------------|---------------|
| HDFS NameNode   | http://localhost:9870     |               |
| Spark Master    | http://localhost:8080     |               |
| Superset        | http://localhost:8088     | admin / admin |

**3. Stop everything**

```bash
docker compose -f docker/docker-compose-superset.yml down
docker compose -f docker/docker-compose-spark.yml down
docker compose -f docker/docker-compose-hdfs.yml down
```

---

## Our implementation (Phase 1 + Building Data Pipeline STUDY)

End-to-end:

```bash
bash scripts/run_pipeline.sh
```

| Step | Script / artifact |
|---|---|
| Download 9 CSVs | `scripts/download_dataset.py` |
| CSV → Parquet on HDFS | `processing/analysis.py` |
| Clean + **star schema** | `processing/build_star_schema.py` |
| Hive register (`olist`, `olist_star`) | `visualization/register_tables.py` |
| Data quality / dedupe report | `processing/data_quality.py` → `reports/data_quality.md` |
| 7 business questions (Python) | `processing/business_questions.py` → `reports/business_answers.md` |
| 7 business questions (SQL) | `sql/business_questions.sql` |
| STUDY write-up (clean/ELT/dbt/layers/star) | `reports/REPORT.md` |

Architecture after transform:

```
CSV → Spark → HDFS raw Parquet → Spark star (fact/dim) → Hive → Superset / SQL
```

---

## Phase 3 — Airflow + dbt Medallion

See full STUDY write-up: [`reports/PHASE3.md`](reports/PHASE3.md)

```bash
bash scripts/run_phase3.sh
# Airflow UI: http://localhost:8089  (admin / admin)
# Trigger DAG: olist_medallion_pipeline
```

| Piece | Path |
|---|---|
| Airflow compose | `docker/docker-compose-airflow.yml` |
| DAG | `airflow/dags/olist_medallion_dag.py` |
| dbt project (Bronze/Silver/Gold) | `dbt/` |
| Phase 3 report | `reports/PHASE3.md` |

```
CSV → Spark Bronze (HDFS) → dbt Silver (clean) → dbt Gold (star) → Superset
         ↑________________ Airflow DAG ________________↑
```

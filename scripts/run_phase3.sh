#!/bin/bash
# Start Phase 3 stack (HDFS + Spark + Airflow) and print next steps.
set -e
cd "$(dirname "$0")/.."

bash scripts/setup_network.sh

# Local secrets file (gitignored) — required for Airflow Fernet key
if [ ! -f .env ]; then
  echo "=== Creating .env with a generated Fernet key ==="
  if python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then
    KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  else
    KEY=$(python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
  fi
  cat > .env <<EOF
AIRFLOW_FERNET_KEY=${KEY}
AIRFLOW_WEBSERVER_SECRET_KEY=dev-only-change-me
AIRFLOW_ADMIN_PASSWORD=admin
SUPERSET_SECRET_KEY=CHANGE_ME_LOCAL_DEV_ONLY
EOF
  echo "Wrote .env (not committed to git)"
fi

echo "=== HDFS ==="
docker compose -f docker/docker-compose-hdfs.yml up -d
sleep 10

echo "=== Spark ==="
docker compose -f docker/docker-compose-spark.yml up -d
sleep 20

echo "=== Airflow (build may take a few minutes) ==="
docker compose --env-file .env -f docker/docker-compose-airflow.yml up -d --build

echo ""
echo "✅ Phase 3 stack starting"
echo "   Airflow : http://localhost:8089  (admin / admin)"
echo "   Trigger DAG: olist_medallion_pipeline"
echo "   Docs    : reports/PHASE3.md"
echo ""
echo "Optional — run dbt only (after ingest + thriftserver up):"
echo "  docker exec -e DBT_SPARK_HOST=spark-thriftserver airflow-scheduler \\"
echo "    bash -c 'cd /opt/airflow/dbt && dbt run --profiles-dir /opt/airflow/dbt'"

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

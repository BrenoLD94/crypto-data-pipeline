#!/bin/sh

# === START KAFKA CONFIG ===

echo "Waiting kafka.."

./wait-for-it.sh broker1:29092 --timeout=60
./wait-for-it.sh broker2:29093 --timeout=30

echo "Creating Kafka topics..."

kafka-topics \
  --create \
  --if-not-exists \
  --topic trades-btc \
  --bootstrap-server broker1:29092,broker2:29093 \
  --partitions 2 \
  --replication-factor 2 \
  --config min.insync.replicas=1

kafka-topics \
  --create \
  --if-not-exists \
  --topic trades-eth \
  --bootstrap-server broker1:29092,broker2:29093 \
  --partitions 2 \
  --replication-factor 2 \
  --config min.insync.replicas=1

# === END KAFKA CONFIG ===

# === START MINIO Config ===

echo "Waiting MinIO..."

./wait-for-it.sh minio:9000 --timeout=60

echo "Creating Minio Buckets..."

mc alias set minio http://minio:9000 $MINIO_USER $MINIO_PASSWORD

mc mb --ignore-existing minio/$MINIO_BUCKET

# === END MINIO Config ===


# === START Postgres Config ===


# === END Postgres Config ===



# === START Supserset Config ===



# === END Supserset Config ===

echo "Infra Setup Finished."

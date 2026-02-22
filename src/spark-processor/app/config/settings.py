# settings.py - File responsible to config env variables
import os

def require_env(name: str) -> str:
    env = os.getenv(name)
    if env is None:
        raise ValueError(f"Environment variable {name} is required!")

    return env

def optional_env(name: str, default: str) -> str:
    env = os.getenv(name, default)

    return env


#variáveis globais spark
SPARK_MASTER_URL = require_env("SPARK_MASTER_URL")

#variáveis globais kafka
KAFKA_TOPIC = require_env("KAFKA_TOPIC")
KAFKA_BOOTSTRAP_SERVERS = require_env("KAFKA_BOOTSTRAP_SERVERS")

# variáveis ambiente influx
INFLUXDB_BUCKET = require_env("INFLUXDB_BUCKET")
INFLUXDB_ORG = require_env("INFLUXDB_ORG")
INFLUXDB_URL= require_env("INFLUXDB_URL")
INFLUXDB_TOKEN = require_env("INFLUXDB_TOKEN")

# variáveis ambiente minio
MINIO_USER = require_env("AWS_ACCESS_KEY_ID")
MINIO_PASSWORD = require_env("AWS_SECRET_ACCESS_KEY")
MINIO_BUCKET = require_env("MINIO_BUCKET")

# variáveis ambiente postgres
POSTGRES_USER= require_env("POSTGRES_USER")
POSTGRES_PASSWORD = require_env("POSTGRES_PASSWORD")
POSTGRES_DB = require_env("POSTGRES_DB")

# variáveis ambiente iceberg
CATALOG_NAME = require_env("CATALOG_NAME")
SCHEMA_NAME = optional_env("SCHEMA_NAME", "raw")
TABLE_NAME = optional_env("TABLE_NAME", "trades")

# variaveis windows parametros
PROCESSING_TIME = require_env("PROCESSING_TIME_WINDOW")
WATERMARK_DELAY = optional_env("WATERMARK_DELAY", "60 seconds")
TIME_WINDOW = optional_env("TIME_WINDOW", "30 seconds")
import pyspark.sql.functions as sf
import influxdb_client
import os

from pyspark.sql import SparkSession
from influxdb_client.client.write_api import SYNCHRONOUS

#variáveis globais kafka
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_BOOSTSTRAP_SERVERS = os.getenv("KAFKA_BOOSTSTRAP_SERVERS")

# variáveis ambiente influx
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_URL= os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")

# variáveis ambiente minio
MINIO_USER = os.getenv("AWS_ACCESS_KEY_ID")
MINIO_PASSWORD = os.getenv("AWS_SECRET_ACCESS_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# variáveis ambiente postgres
POSTGRES_USER= os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

CATALOG_NAME = os.getenv("CATALOG_NAME")
PROCESSING_TIME_WINDOW = os.getenv("PROCESSING_TIME_WINDOW")


def get_spark_session(postgres_user, 
                      postgres_password,
                      minio_user, 
                      minio_password,
                      catalog_name, 
                      postgres_db="iceberg", 
                      minio_bucket_name="cripto-data"):

    spark = SparkSession \
        .builder \
        .appName("cryptoDataPipelineStreaming") \
        .master("spark://spark-master:7077") \
        .config("spark.sql.caseSensitive", "true") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config(f"spark.sql.catalog.{catalog_name}", "org.apache.iceberg.spark.SparkCatalog") \
        .config(f"spark.sql.catalog.{catalog_name}.type", "jdbc") \
        .config(f"spark.sql.catalog.{catalog_name}.warehouse", f"s3a://{minio_bucket_name}/") \
        .config(f"spark.sql.catalog.{catalog_name}.uri", f"jdbc:postgresql://postgres:5432/{postgres_db}") \
        .config(f"spark.sql.catalog.{catalog_name}.jdbc.verifyServerCertificate", "False") \
        .config(f"spark.sql.catalog.{catalog_name}.jdbc.useSSL", "False") \
        .config(f"spark.sql.catalog.{catalog_name}.jdbc.user", postgres_user) \
        .config(f"spark.sql.catalog.{catalog_name}.jdbc.password", postgres_password) \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", minio_user) \
        .config("spark.hadoop.fs.s3a.secret.key", minio_password) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()
    
    return spark


def write_influxdb_not_optimizer(batch_df, batch_id):

    # =============== HOT PATH =====================
    print(f"--- Processando Lote ID: {batch_id} ---")
    
    client = influxdb_client.InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)

    df = batch_df.toPandas()

    points = []
    for index, row in df.iterrows():
        p = influxdb_client.Point("trades_summary") \
            .tag("symbol", row['symbol']) \
            .field("total_quantity", row['total_quantity']) \
            .field("average_price", row['average_price']) \
            .time(row.window['start'])
        
        points.append(p)
    
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
    
    print(f"Lote {batch_id} com {len(df)} linhas escrito no InfluxDB.")
    
    client.close()

def write_influxdb(iterator_of_rows):
    client = influxdb_client.InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)

    points = []
    for row in iterator_of_rows:
        p = influxdb_client.Point("trades_summary") \
            .tag("symbol", row['symbol']) \
            .field("total_quantity", row['total_quantity']) \
            .field("average_price", row['average_price']) \
            .time(row.window['start'])
        
        points.append(p)
    
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)

    client.close()
    
def write_raw_to_iceberg(batch_df, batch_id):
      # =============== COLD PATH =====================
    try:
        print(f"--- Escrevendo lote {batch_id} no Iceberg (Cold Path) ---")
        
        batch_df = batch_df.withColumn("trade_date", sf.to_date(sf.col("event_timestamp")))

        table_name = f"{CATALOG_NAME}.raw.trades"

        if batch_df.sparkSession.catalog.tableExists(table_name):
            batch_df.writeTo(table_name) \
            .partitionedBy("symbol", "trade_date") \
            .append()
        else:
            batch_df.writeTo(table_name) \
            .partitionedBy("symbol", "trade_date") \
            .create()
        
        
        print(f"--- Lote {batch_id} escrito no Iceberg com sucesso. ---")
    
    except Exception as e:
        print(f"Erro ao escrever no Iceberg: {e}")

    # Libera o DataFrame da memória
    batch_df.unpersist()

def write_raw_to_minio(batch_df, batch_id):
    """
    Salva um micro-lote de dados brutos como arquivos Parquet no MinIO.
    """
    print(f"--- Escrevendo lote BRUTO {batch_id} como Parquet no MinIO ---")
    try:
        # Adiciona a coluna de data para particionar as pastas
        df_for_writing = batch_df.withColumn("trade_date", sf.to_date(sf.col("event_timestamp")))
        
        # Define o caminho de destino no MinIO
        output_path = f"s3a://{MINIO_BUCKET}/streaming/"

        # Escreve o DataFrame no formato Parquet
        df_for_writing.write \
            .mode("append") \
            .partitionBy("symbol", "trade_date") \
            .parquet(output_path)
        
        print(f"--- Lote BRUTO {batch_id} escrito com sucesso em '{output_path}' ---")
    
    except Exception as e:
        print(f"!!! Erro ao escrever no MinIO: {e}")


def create_schema_iceberg_if_not_exist(spark, catalog_name, schema_name):
    """
    Cria um Schema (também chamado de Database ou Namespace) no catálogo Iceberg.
    Isso cria a estrutura lógica necessária antes de criar tabelas.
    """

    print(f"--- Criando Schema Iceberg: {catalog_name}.{schema_name} ---")

    spark.sql(f"CREATE DATABASE IF NOT EXISTS {catalog_name}.{schema_name}")

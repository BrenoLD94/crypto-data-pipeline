# bibliotecas built-in
import pyspark.sql.functions as sf
import os
import logging
from pyspark.sql import SparkSession

# bibliotecas customizadas
from utils.logging_config import setup_logging
from schema.schema import create_table_iceberg_if_not_exists
from config.settings import POSTGRES_USER, POSTGRES_PASSWORD, MINIO_USER, MINIO_PASSWORD, CATALOG_NAME, POSTGRES_DB, MINIO_BUCKET, KAFKA_BOOTSTRAP_SERVERS, SCHEMA_NAME, TABLE_NAME, WATERMARK_DELAY, TIME_WINDOW, PROCESSING_TIME,SPARK_MASTER_URL
from sources.kafka import read_kafka_stream
from transform.transformations import apply_transformation, add_watermark
from sink.iceberg import spark_write_minio_using_iceberg
from sink.influxdb import spark_write_influxdb


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
        .master(SPARK_MASTER_URL) \
        .config("spark.sql.caseSensitive", "true") \
        .config("startingOffsets", "latest") \
        .config("maxOffsetsPerTrigger", "50000") \
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

setup_logging()


def main():
    logger = logging.getLogger(__name__)

    logger.info("Iniciando Pipeline! ...")

    spark = get_spark_session(postgres_user = POSTGRES_USER,
                            postgres_password = POSTGRES_PASSWORD,
                            minio_user=MINIO_USER,
                            minio_password=MINIO_PASSWORD,
                            catalog_name=CATALOG_NAME, 
                            postgres_db=POSTGRES_DB,
                            minio_bucket_name = MINIO_BUCKET)

    create_table_iceberg_if_not_exists(spark = spark, 
                                       catalog_name = CATALOG_NAME, 
                                       schema_name = SCHEMA_NAME, 
                                       table_name = TABLE_NAME)

    binance_trades_raw = read_kafka_stream(spark, KAFKA_BOOTSTRAP_SERVERS) 

    cleaned_df = apply_transformation(binance_trades_raw)

    spark_write_minio_using_iceberg(cleaned_df, 
                                    minio_bucket=MINIO_BUCKET, 
                                    iceberg_schema_name=SCHEMA_NAME, 
                                    iceberg_table_name=TABLE_NAME, 
                                    processing_time=PROCESSING_TIME)

    df_with_watermark = add_watermark(cleaned_df, 
                                      watermark_delay=WATERMARK_DELAY, 
                                      time_window=TIME_WINDOW)
    
    spark_write_influxdb(df_with_watermark, 
                         minio_bucket=MINIO_BUCKET, 
                         processing_time=PROCESSING_TIME)


    # Mantém a aplicação viva, esperando o stream terminar
    spark.streams.awaitAnyTermination()

    logger.info("Finalizando Pipeline! ...")

if __name__ == "__main__":
    main()
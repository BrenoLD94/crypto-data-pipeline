# iceberg_sink.py - file responsible to write data in iceberg
import pyspark.sql.functions as sf
import logging

from config.settings import CATALOG_NAME

logger = logging.getLogger(__name__)

def write_minio_using_iceberg(batch_df, batch_id, schema_name, table_name):
    try:
        logger.info(f"--- Escrevendo lote {batch_id} no Iceberg ---")
        
        full_table_name = f"{CATALOG_NAME}.{schema_name}.{table_name}"
        
        total_records = batch_df.counts()

        batch_df.writeTo(full_table_name) \
            .append()
        
        logger.info(f"--- Lote {batch_id} escreveu {total_records} registros na tabela {full_table_name} do Iceberg com sucesso! ---")
    
    except Exception as e:
        logger.exception(f"Error to write in Iceberg")


def spark_write_minio_using_iceberg(df, minio_bucket, iceberg_schema_name, iceberg_table_name, processing_time, checkpoint_location="spark_checkpoints/cold_path_sink"):
    # SINK - COLD PATH
    query = df.writeStream \
        .outputMode("append") \
        .foreachBatch(lambda batch_df, batch_id: write_minio_using_iceberg(batch_df, batch_id, iceberg_schema_name, iceberg_table_name)) \
        .option("checkpointLocation", f"s3a://{minio_bucket}/{checkpoint_location}") \
        .trigger(processingTime=processing_time) \
        .start()
    
    return query 

import pyspark.sql.functions as sf
import os

from pyspark.sql.types import StructType,StructField, StringType, IntegerType, BooleanType, FloatType, LongType

# importando variáveis de ambiente globais
from utils import KAFKA_TOPIC, KAFKA_BOOSTSTRAP_SERVERS, INFLUXDB_BUCKET, INFLUXDB_ORG, INFLUXDB_URL, INFLUXDB_TOKEN, MINIO_USER, MINIO_PASSWORD, MINIO_BUCKET, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, CATALOG_NAME, PROCESSING_TIME_WINDOW
# importando funções auxiliares
from utils import get_spark_session, write_influxdb, write_raw_to_iceberg, create_schema_iceberg_if_not_exist

#{
#    "stream":"btcusdt@aggTrade",
#    "data":{"e":"aggTrade","E":1752193668853,"a":2782814634,"s":"BTCUSDT","p":"115239.90","q":"0.070","f":6460726680,"l":6460726680,"T":1752193668763,"m":true}
#}

# {
#   "e": "aggTrade",  // Event type
#   "E": 123456789,   // Event time
#   "s": "BTCUSDT",    // Symbol
#   "a": 5933014,		// Aggregate trade ID
#   "p": "0.001",     // Price
#   "q": "100",       // Quantity
#   "f": 100,         // First trade ID
#   "l": 105,         // Last trade ID
#   "T": 123456785,   // Trade time
#   "m": true,        // Is the buyer the market maker?
# }


def main():
    spark = get_spark_session(postgres_user = POSTGRES_USER,
                            postgres_password = POSTGRES_PASSWORD,
                            minio_user=MINIO_USER,
                            minio_password=MINIO_PASSWORD,
                            catalog_name=CATALOG_NAME, 
                            postgres_db=POSTGRES_DB,
                            minio_bucket_name = MINIO_BUCKET)

    user_schema = StructType([ \
        StructField("e", StringType(), True), \
        StructField("E", LongType(), True), \
        StructField("s", StringType(), True), \
        StructField("a", LongType(), True), \
        StructField("p", StringType(), True), \
        StructField("q", StringType(), True), \
        StructField("f", LongType(), True), \
        StructField("l", LongType(), True), \
        StructField("T", LongType(), True), \
        StructField("m", BooleanType(), True)
      ])

    create_schema_iceberg_if_not_exist(spark, catalog_name= CATALOG_NAME, schema_name="raw")

    # defining source
    binance_df_raw = spark \
                    .readStream \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", KAFKA_BOOSTSTRAP_SERVERS) \
                    .option("subscribePattern", "trades-.*") \
                    .load()

    # 1. Cast para String
    df_string = binance_df_raw.selectExpr("CAST(value as STRING) AS value")

    # 2. Extrai o JSON de dentro do campo 'data'
    df_data_str = df_string.select(sf.get_json_object(sf.col("value"), "$.data").alias("data_str"))

    # 3. Aplica o schema na nova coluna e expande para colunas finais
    df_final_cols = df_data_str.select(sf.from_json(sf.col("data_str"), user_schema).alias("data_struct")) \
                               .select("data_struct.*")

    # 4. Renomeia as colunas
    df_renamed = df_final_cols.withColumnRenamed("e", "event_type") \
                            .withColumnRenamed("E", "event_time") \
                            .withColumnRenamed("s", "symbol") \
                            .withColumnRenamed("a", "agg_trade_id") \
                            .withColumnRenamed("p" , "price") \
                            .withColumnRenamed("q", "quantity") \
                            .withColumnRenamed("f", "first_trade_id") \
                            .withColumnRenamed("l", "last_trade_id") \
                            .withColumnRenamed("T", "trade_time") \
                            .withColumnRenamed("m", "is_buyer_market")


    df_casted = df_renamed.withColumn("quantity", sf.col("quantity").cast("double")) \
                        .withColumn("price", sf.col("price").cast("double"))

    # 5. Estruturando coluna de event time
    df_with_timestamp = df_casted.withColumn("event_timestamp", (sf.col("event_time") / 1000).cast("double").cast("timestamp") )

    # SINK - COLD PATH
    query_raw = df_with_timestamp.writeStream \
        .outputMode("append") \
        .foreachBatch(write_raw_to_iceberg) \
        .option("checkpointLocation", f"s3a://{MINIO_BUCKET}/spark_checkpoints/cold_path_sink") \
        .trigger(processingTime=PROCESSING_TIME_WINDOW) \
        .start()


    # 6. Aplicando window function e agregações
    df_windowed = df_with_timestamp.withWatermark("event_timestamp", "60 seconds").groupBy(
        sf.col("symbol"),
        sf.window(sf.col("event_timestamp"), "30 seconds")
    ).agg(
        sf.sum("quantity").alias("total_quantity"), 
        sf.avg("price").alias("average_price")
    )

    # SINK - HOT PATH
    query_aggregated = df_windowed.writeStream \
        .outputMode("update") \
        .foreachBatch(lambda batch_df, batch_id: batch_df.foreachPartition(write_influxdb)) \
        .option("checkpointLocation", f"s3a://{MINIO_BUCKET}/spark_checkpoints/influxdb_sink") \
        .trigger(processingTime=PROCESSING_TIME_WINDOW) \
        .start()


    # 8. Mantém a aplicação viva, esperando o stream terminar
    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    main()
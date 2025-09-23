from pyspark.sql import SparkSession
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, BooleanType, FloatType, LongType
import pyspark.sql.functions as sf

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

import os

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

KAFKA_TOPIC = "binance-trades-raw"
KAFKA_BOOSTSTRAP_SERVERS = "kafka:29092"
INFLUXDB_BUCKET = "trades_raw"
INFLUXDB_ORG = "crypto_pipeline_org"
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_URL="http://influxdb:8086"

def get_spark_session(catalog_name="cripto_data", 
                      postgres_user="breno", 
                      postgres_password="admin2025", 
                      postgres_db="criptoDB", 
                      minio_user="breno", 
                      minio_password="admin2025",
                      minio_bucket_name = "cripto-data"):

    spark = SparkSession \
            .builder \
            .appName("cryptoDataPipelineStreaming") \
            .master("spark://spark-master:7077") \
            .config("spark.sql.caseSensitive", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config(f"spark.sql.catalog.{catalog_name}", "org.apache.iceberg.spark.SparkCatalog") \
            .config(f"spark.sql.catalog.{catalog_name}.type", "jdbc") \
            .config(f"spark.sql.catalog.{catalog_name}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
            .config(f"spark.sql.catalog.{catalog_name}.warehouse", f"s3a://{minio_bucket_name}/") \
            .config(f"spark.sql.catalog.{catalog_name}.uri", f"jdbc:postgresql://postgres:5432/{postgres_db}") \
            .config(f"spark.sql.catalog.{catalog_name}.jdbc.verifyServerCertificate", "False") \
            .config(f"spark.sql.catalog.{catalog_name}.jdbc.useSSL", "False") \
            .config(f"spark.sql.catalog.{catalog_name}.jdbc.user", postgres_user) \
            .config(f"spark.sql.catalog.{catalog_name}.jdbc.password", postgres_password) \
            .config("spark.hadoop.fs.s3a.access.key", minio_user) \
            .config("spark.hadoop.fs.s3a.secret.key", minio_password) \
            .config("spark.hadoop.fs.s3a.region", "us-east-1") \
            .config("spark.hadoop.fs.s3a.path.style.access", "True") \
            .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
            .getOrCreate()
    
    return spark

def write_influxdb(batch_df, batch_id):

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

def write_raw_to_iceberg(batch_df, batch_id):
      # =============== COLD PATH =====================
    try:
        print(f"--- Escrevendo lote {batch_id} no Iceberg (Cold Path) ---")
        
        batch_df = batch_df.withColumn("trade_date", sf.to_date(sf.col("event_timestamp")))

        table_name = "cripto_data.bronze.trades_agg"

        if batch_df.sparkSession.catalog.tableExists(table_name):
            batch_df.writeTo(table_name) \
            .partitionedBy("trade_date") \
            .append()
        else:
            batch_df.writeTo(table_name) \
            .partitionedBy("trade_date") \
            .create()
        
        
        print(f"--- Lote {batch_id} escrito no Iceberg com sucesso. ---")
    
    except Exception as e:
        print(f"Erro ao escrever no Iceberg: {e}")

    # Libera o DataFrame da memória
    batch_df.unpersist()
    

def main():

    spark = get_spark_session()

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

    # defining source
    binance_df_raw = spark \
                    .readStream \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", KAFKA_BOOSTSTRAP_SERVERS) \
                    .option("subscribe", KAFKA_TOPIC) \
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
    df_with_timestamp = df_casted.withColumn("event_timestamp", (sf.col("event_time") / 1000).cast("timestamp") )

    # SINK - COLD PATH
    query_raw = df_with_timestamp.writeStream \
        .outputMode("append") \
        .foreachBatch(write_raw_to_iceberg) \
        .option("checkpointLocation", "/tmp/spark_checkpoints/cold_path_sink") \
        .trigger(processingTime='15 seconds') \
        .start()


    # 6. Aplicando window function e agregações
    df_windowed = df_with_timestamp.withWatermark("event_timestamp", "15 seconds").groupBy(
        sf.col("symbol"),
        sf.window(sf.col("event_timestamp"), "10 seconds")
    ).agg(
        sf.sum("quantity").alias("total_quantity"), 
        sf.avg("price").alias("average_price")
    )

    # SINK - HOT PATH
    query_aggregated = df_windowed.writeStream \
        .outputMode("update") \
        .foreachBatch(write_influxdb) \
        .option("checkpointLocation", "/tmp/spark_checkpoints/influxdb_sink") \
        .trigger(processingTime='15 seconds') \
        .start()


    # 8. Mantém a aplicação viva, esperando o stream terminar
    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    main()
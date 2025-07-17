from pyspark.sql import SparkSession
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, BooleanType, FloatType, LongType
import pyspark.sql.functions as sf

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

import os

#  https://spark.apache.org/docs/latest/streaming/getting-started.html#programming-model -> leia isso
#  https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html#window-operations-on-event-time 

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

spark = SparkSession \
        .builder \
        .appName("cryptoDataPipelineStreaming") \
        .master("spark://spark-master:7077") \
        .config("spark.sql.caseSensitive", "true") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .getOrCreate()

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

# 6. Aplicando window function e agregações
df_windowed = df_with_timestamp.withWatermark("event_timestamp", "15 seconds").groupBy(
    sf.col("symbol"),
    sf.window(sf.col("event_timestamp"), "10 seconds")
).agg(
    sf.sum("quantity").alias("total_quantity"), 
    sf.avg("price").alias("average_price")
)

df_windowed.printSchema()

INFLUXDB_BUCKET = "trades_raw"
INFLUXDB_ORG = "crypto_pipeline_org"
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_URL="http://influxdb:8086"

def write_influxdb(batch_df, batch_id):
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

# 7. Inicia o sink (saída) para o console
query = df_windowed.writeStream \
    .foreachBatch(write_influxdb) \
    .option("checkpointLocation", "/tmp/spark_checkpoints/influxdb_sink") \
    .trigger(processingTime='15 seconds') \
    .start()

# 8. Mantém a aplicação viva, esperando o stream terminar
query.awaitTermination()
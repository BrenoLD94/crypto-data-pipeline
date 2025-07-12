from pyspark.sql import SparkSession
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, BooleanType, FloatType
import pyspark.sql.functions as sf

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
        .getorcreate()

user_schema = StructType([ \
    StructField("e", StringType(), True), \
    StructField("E", IntegerType(), True), \
    StructField("s", StringType(), True), \
    StructField("a", IntegerType(), True), \
    StructField("p", FloatType(), True), \
    StructField("q", IntegerType(), True), \
    StructField("f", IntegerType(), True), \
    StructField("l", IntegerType(), True), \
    StructField("T", IntegerType(), True), \
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
df_data_str = df_string.select(sf.from_json(sf.get_json_object(sf.col("value"), "$.data"))).alias("data_str")

# 3. Aplica o schema na nova coluna e expande para colunas finais
df_final_cols = df_data_str.select(sf.from_json(sf.col("data_str"), user_schema).alias("data_struct")) \
                           .select("data_struct.*")

# 4. Renomeia as colunas
df_renamed = df_final_cols.withColumnRenamed("e", "event_type") \
                        .withColumnRenamed("E", "event_time") \
                        .withColumnRenamed("s", "symbol") \
                        .withColumnRenamed("a", "agg_trade_id") \
                        .withColumnRenamed("p" , "Price") \
                        .withColumnRenamed("q", "quantity") \
                        .withColumnRenamed("f", "first_trade_id") \
                        .withColumnRenamed("l", "last_trade_id") \
                        .withColumnRenamed("T", "trade_time") \
                        .withColumnRenamed("m", "is_buyer_market")


# 5. Inicia o sink (saída) para o console
query = df_renamed.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# 6. Mantém a aplicação viva, esperando o stream terminar
query.awaitTermination()
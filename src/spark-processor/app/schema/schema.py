# schema.py - file define schemas 

from pyspark.sql.types import StructType,StructField, StringType, BooleanType, LongType


ROW_LEVEL_SCHEMA = StructType([ \
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
    
ROW_OUTER_LEVEL_SCHEMA = StructType(
    [
        StructField("stream", StringType()), \
        StructField("data", ROW_LEVEL_SCHEMA)
    ]
)


def create_table_iceberg_if_not_exists(spark, catalog_name, schema_name, table_name):
    # cria o schema no iceberg se não existir
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog_name}.{schema_name}.{table_name} (
            event_type STRING,
            event_time LONG,
            symbol STRING,
            agg_trade_id LONG,
            price STRING,
            quantity STRING,
            first_trade_id LONG,
            last_trade_id LONG,
            trade_time LONG,
            is_buyer_market BOOLEAN,
            event_timestamp TIMESTAMP,
            trade_date DATE
        ) USING iceberg
        PARTITIONED BY (symbol, trade_date)
    """)


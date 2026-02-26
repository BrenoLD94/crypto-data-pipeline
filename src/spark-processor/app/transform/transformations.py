# transformations.py - file responsible to apply business transformation

import pyspark.sql.functions as sf

from schema.schema import ROW_OUTER_LEVEL_SCHEMA

def apply_transformation(df):

    df_expanded_cols = df.select(sf.from_json(sf.col("value"), ROW_OUTER_LEVEL_SCHEMA).alias("json"))\
                        .select("json.data.*")

    df_cleaned = (
        df_expanded_cols.select(
            sf.col("e").alias("event_type"),
            sf.col("E").alias("event_time"), 
            sf.col("s").alias("symbol"), 
            sf.col("a").alias("agg_trade_id"), 
            sf.col("p").cast("double").alias("price"), 
            sf.col("q").cast("double").alias("quantity"), 
            sf.col("f").alias("first_trade_id"), 
            sf.col("l").alias("last_trade_id"), 
            sf.col("T").alias("trade_time"), 
            sf.col("m").alias("is_buyer_market")
        ).withColumn(
            "event_timestamp",
            (sf.col("event_time") / 1000).cast("timestamp")
        ).withColumn(
            "trade_date",
            sf.col("event_timestamp").cast("date")
        )
    )

    return df_cleaned

def add_watermark(df, watermark_delay = "60 seconds", time_window = "30 seconds"):
    # Aplicando window function e agregações
    df_windowed = df.withWatermark("event_timestamp", watermark_delay).groupBy(
        sf.col("symbol"),
        sf.window(sf.col("event_timestamp"), time_window)
    ).agg(
        sf.sum("quantity").alias("total_quantity"), 
        sf.avg("price").alias("average_price")
    )

    return df_windowed


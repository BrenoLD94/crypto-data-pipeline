# kafka.py - file with definition how to read data from Kafka
import logging

logger = logging.getLogger(__name__)

def read_kafka_stream(spark, 
                      kafka_bootstrap_servers: str, 
                      pattern: str = "trades-.*",
                      starting_offsets: str = "earliest",
                      fail_on_data_loss: str = "true"):
    
    logger.info(
        f"Initializing Kafka stream | "
        f"servers={kafka_bootstrap_servers} | "
        f"pattern={pattern} | "
        f"startingOffsets={starting_offsets}"
    )

    try:
        df = spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
                .option("subscribePattern", pattern) \
                .option("startingOffsets", starting_offsets) \
                .option("failOnDataLoss", fail_on_data_loss) \
                .load()
        
        df = df.selectExpr(
                "CAST(key AS STRING) AS key",
                "CAST(value AS STRING) AS value",
                "topic",
                "partition",
                "offset",
                "timestamp"
            )

        return df
    
    except Exception as e:
        logger.exception("Fail to read data from kafka")
        raise
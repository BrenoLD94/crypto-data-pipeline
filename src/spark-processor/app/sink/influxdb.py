# influxdb_sink.py - file responsible to write data in InfluxDB

import influxdb_client
import logging

from influxdb_client.client.write_api import SYNCHRONOUS
from config.settings import INFLUXDB_ORG, INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_BUCKET


logger = logging.getLogger(__name__)
_client = None
_write_api = None

def get_client():
    global _client, _write_api

    if _client is None:
        _client = influxdb_client.InfluxDBClient(
                url=INFLUXDB_URL,
                token=INFLUXDB_TOKEN,
                org=INFLUXDB_ORG
            )

        _write_api = _client.write_api(write_options=SYNCHRONOUS)
    
    return _write_api


def write_influxdb(iterator_of_rows):
    write_api = get_client()

    try:
        points = []
        buffer_size = 10000
        for row in iterator_of_rows:
            p = influxdb_client.Point("trades_summary") \
                .tag("symbol", row['symbol']) \
                .field("total_quantity", row['total_quantity']) \
                .field("average_price", row['average_price']) \
                .time(row.window['start'])

            points.append(p)
            if len(points) >= buffer_size:
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
                points = []

        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
    
    except Exception as e:
        logger.exception(f'Error to connect/write to influxDB: {e}')
        raise 



def spark_write_influxdb(df, minio_bucket, processing_time, checkpoint_location = "spark_checkpoints/influxdb_sink"):

    # SINK - HOT PATH
    query = df.writeStream \
        .outputMode("update") \
        .foreachBatch(lambda batch_df, batch_id: batch_df.foreachPartition(write_influxdb)) \
        .option("checkpointLocation", f"s3a://{minio_bucket}/{checkpoint_location}") \
        .trigger(processingTime=processing_time) \
        .start()
    
    return query

from confluent_kafka import Producer

# https://developer.confluent.io/get-started/python/#build-producer
def main():
    producer_config = {"bootstrap.servers": "kafka:9092"}
    topic = "binance-trades-raw"
    key = "BTCUSDT"
    value = "minha primeira mensagem kafka!"

    producer = Producer(producer_config)

    producer.produce(topic, value=value.encode("utf-8"), key=key.encode("utf-8"))

    producer.flush()

if __name__ == "__main__":
    main()
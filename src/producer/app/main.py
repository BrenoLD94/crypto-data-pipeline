import logging
import time
import json 

from confluent_kafka import Producer
from binance.lib.utils import config_logging
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

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

PRODUCER_CONFIG = {"bootstrap.servers": "kafka:29092"}
PRODUCER = Producer(PRODUCER_CONFIG)
KAFKA_TOPIC = "binance-trades-raw"

# https://developer.confluent.io/get-started/python/#build-producer
# https://github.com/binance/binance-futures-connector-python/blob/main/examples/websocket/um_futures/agg_trade.py

def message_handler(_, message):
    data = json.loads(message)

    key = data.get('s')

    if key:
        print(f"Trade recebido para {key}: {message}")

        PRODUCER.produce(KAFKA_TOPIC, key=key.encode('utf-8'), value=message.encode('utf-8'))

        PRODUCER.flush()

def main():
    config_logging(logging, logging.DEBUG)

    key = "btcusdt"#"BTCUSDT"

    # Crie a instância do BINANCE_CLIENT, passando o 'message_handler'
    binance_client = UMFuturesWebsocketClient(on_message=message_handler, is_combined=True)
    
    # Inscreva-se no stream UMA VEZ
    logging.info("Inscrevendo no stream de aggTrade para BTCUSDT...")
    binance_client.agg_trade(symbol=key)

    while True:
        # A thread do WebSocket está rodando em segundo plano.
        # O loop principal pode apenas esperar.
        time.sleep(1)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaindo...")

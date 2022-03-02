import pickle
from celery import Celery
import redis
from backend.operations.binance_futures import BinanceFuturesOps
from backend.utils.binance.streams import ThreadedWebsocketManager
from config import Config
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL,
                backend=Config.CELERY_BROKER_URL)

red = redis.from_url(Config.REDIS_URL)


def startPriceStreams(api_key, api_secret, symbol, rediskeyname):
    # Update the bookTicker price of the trading symbols
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)

    def handle_socket_message(price_data):
        print(price_data)

        # twm.stop()

    twm.start()

    twm.start_symbol_ticker_futures_socket(
        callback=handle_socket_message, symbol=symbol)

api_key = "02eTTLVw9T6g3oEmelloLP3IGt8QlCoCOKvdWshpKU1KWOQ7sDIm2xrDOPe3X9S6 "
api_secret = "MjP6qfoCnLX8KeIFAzW0KyE3LL96xlbbTYI962pWtyaES4SBIWiJXBJ1S3uMwoS8"
# startPriceStreams(api_key, api_secret, "ATOMUSDT", 'rediskeyname')


api_key = "02eTTLVw9T6g3oEmelloLP3IGt8QlCoCOKvdWshpKU1KWOQ7sDIm2xrDOPe3X9S6 "
api_secret = "MjP6qfoCnLX8KeIFAzW0KyE3LL96xlbbTYI962pWtyaES4SBIWiJXBJ1S3uMwoS8"

test = BinanceFuturesOps(api_key=api_key,api_secret=api_secret, trade_symbol="BTCUSDT" )
info = test.get_account()
print(info)
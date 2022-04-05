import json
import requests
import redis
import random
from config import Config

from backend.operations.text_parser import processDataFor3commas

red = redis.from_url(Config.REDIS_URL)
raw_signal = {
    "reduceOnly": False,
    "closeOrder": False,
    "forceHold": False,
    "hidden": False,
    "iceberg": False,
    "leverage": 20,
    "postOnly": False,
    "remark": "remark",
    "side": "buy",
    "size": 1,
    "stop": "",
    "stopPrice": 0,
    "stopPriceType": "",
    "symbol": "JASYMUSDT",
    "timeInForce": "",
    "type": "market",
    "visibleSize": 0
}

def stream(raw_signal):
    # data =processDataFor3commas(raw_signal)
    # if data is not False:
<<<<<<< HEAD
    red.publish('smart-signals-kucoin-order',json.dumps(raw_signal))
=======
    red.publish('smart-signals',json.dumps(raw_signal))
>>>>>>> 89d6c85a182eeb54ca1eb27e4f53187dc2c382f4

if __name__ == '__main__':
    stream(raw_signal)
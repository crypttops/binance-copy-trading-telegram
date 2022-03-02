import json
import requests
import redis
import random
from config import Config

from backend.operations.text_parser import processDataFor3commas

red = redis.from_url(Config.REDIS_URL)
raw_signal = """
        ATOM/USDT LONG 
        Leverage 20x
        Entries 30.650
        Target 1 32.388
        Target 2 32.600
        SL 30.160
        """

def stream(raw_signal):
    data =processDataFor3commas(raw_signal)
    if data is not False:
        red.publish('smart-signals',json.dumps(data))

if __name__ == '__main__':
    stream(raw_signal)
import json
import requests
import redis
import random
from config import Config

from backend.operations.text_parser import processDataFor3commas

red = redis.from_url(Config.REDIS_URL)
raw_signal = """
        REN/USDT LONG 
        Leverage 20x
        Entries 0.4421
        Target 1 0.4460
        Target 2 0.4470
        SL 30.160
        """

def stream(raw_signal):
    data =processDataFor3commas(raw_signal)
    if data is not False:
        red.publish('smart-signals',json.dumps(data))

if __name__ == '__main__':
    stream(raw_signal)
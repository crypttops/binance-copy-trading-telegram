import json
import requests
import redis
import random
from config import Config

from backend.operations.text_parser import processDataFor3commas

red = redis.from_url(Config.REDES_SUB_URL)
raw_signal = """
        OGN/USDT SHORT 
        Leverage 20x
        Entries 0.540
        Target 1 0.465
        Target 2 0.454
        Target 3 0.437
        Target 4 0.380
        Target 5 0.359

        SL 0.507
        """

def stream(raw_signal):
    data =processDataFor3commas(raw_signal)
    if data is not False:
        red.publish('smart-signals',json.dumps(data))

if __name__ == '__main__':
    stream(raw_signal)
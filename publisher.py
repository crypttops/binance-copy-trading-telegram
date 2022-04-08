import json
import requests
import redis
import random
from config import Config

from backend.operations.text_parser import processDataFor3commas

red = redis.from_url(Config.REDES_SUB_URL)
raw_signal = {
    "symbol":"WAVESUSDTM"
}

def stream(raw_signal):
    # data =processDataFor3commas(raw_signal)
    # if data is not False:
    red.publish('smart-signals-kucoin-close',json.dumps(raw_signal))

if __name__ == '__main__':
    stream(raw_signal)
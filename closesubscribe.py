import json
from operator import pos
import pickle
from pydoc_data.topics import topics
import queue
from typing import Dict
from backend.operations.binance import cancelAllPositionBySymbol
from backend.operations.binance_futures import BinanceFuturesOps
import threading
from app import app
from backend.operations.bot import sendMessage
from backend.operations.db import getAllUserConfigs
import redis
from backend.operations.price import convert_usdt_to_base_asset, get_last_price_ticker

from config import Config
from tasks import startPriceStreams

red = redis.from_url(Config.REDIS_URL)
redsub= redis.from_url(Config.REDES_SUB_URL)
bot_token = Config.BOT_TOKEN


    
def user_counter():

    sub = redsub.pubsub()
    sub.subscribe('smart-signals-kucoin-close-2')
    for signal_data in sub.listen():
        if signal_data is not None and isinstance(signal_data, dict):
            try:
                close_data = json.loads(signal_data['data'])
                close_data['symbol']=close_data['symbol'][:-1]
                
                with app.app_context():
                    users = getAllUserConfigs()
                    print(users)
                    
                if users ==[]:#if no data
                    pass
                else:
                    # close order method
                    for user in users:
                        pass
                        # response = cancelAllPositionBySymbol(user.key, user.secret, close_data['symbol'])
                        # if response:
                        #     sendMessage(user.telegram_id, f"All orders and positions for {close_data['symbol']} closed successfully.")
                        # else:
                        #     sendMessage(user.telegram_id, f"You have no open positions for {close_data['symbol']}")

                    print ("done" )   
            except Exception as e:
                print("error found", str(e))

while True:
  user_counter()
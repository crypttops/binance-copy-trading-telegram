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
    sub.subscribe('smart-signals-close')
    for signal_data in sub.listen():
        if signal_data is not None and isinstance(signal_data, dict):
            try:
                command = json.loads(signal_data['data'])
                print(command)
                command_close=command.split('-')
                print(command_close)
                close_data =json.loads(command_close[1])
            
                print(close_data)

                rediskeyname = str(float(close_data['price']))
                print("Rediskeyname", rediskeyname)
                userorderdetails = pickle.loads(red.get(rediskeyname))
                # userdetails = [{'key':'Dl5u9FNa2BR5H0SXfzD9BAT6wPRdL6iuceVOCCT8IkLlaaT2C2Ko5ySmuz4Z0j6c','secret': 'IB1z4Kz55GrxXBfGWwl54yJZcvjGcRZlZgSc0KLMWqrgUJIzKo0DfiGKSKLSvAOW', 'telegram_id':'1499548874' }]
                position_cancel_params=userorderdetails['position_close_data']
                # position_cancel_params = {'symbol': 'RENUSDT', 'type': 'MARKET', 'side': 'SELL', 'quantity':None}
                userdetails = userorderdetails['users']
                print("The are the details to use to place the orders", userdetails)
                for user_order_details in userdetails:
                    api_key =user_order_details['key']
                    api_secret = user_order_details['secret']

                    telegram_id = user_order_details['telegram_id']
                    # close order method
                    with app.app_context():
                        response = cancelAllPositionBySymbol(telegram_id,api_key, api_secret, close_data['symbol'], position_cancel_params)
                    if response:
                        sendMessage(telegram_id, f"All orders and positions for {close_data['symbol']} closed successfully.")
                    else:
                        sendMessage(telegram_id, f"You have no open positions for {close_data['symbol']}")

                red.delete(rediskeyname)
                print(f"Done processing deleting cache for {rediskeyname} from memory" )

                        
            except Exception as e:
                print("error found", str(e))

while True:
  user_counter()
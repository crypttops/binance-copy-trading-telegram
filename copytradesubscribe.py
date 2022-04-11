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

Data =[]



def send_orders(api_key, api_secret, qty, data, telegram_id):
    print(f"Executing order for {telegram_id}")
    print("Data in send order", data)
    print("quantity", qty)
    """
    #Order template
    """
    print(data)
    trade_symbol= data['position']['symbol']
    client = BinanceFuturesOps(api_key=api_key, api_secret=api_secret, trade_symbol=trade_symbol)
   
    data["position"]["quantity"]=float(qty)
    print("Data after updating the quantiy", data)
    
    # send the position order
    position_params = data["position"]
    print("the data, ", position_params)
    try:
        resp = client.sendOrder(position_params)
        print("the response",resp)
        position_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT placed successfully"
        sendMessage(telegram_id, position_resp )
        # results = tps_n_sls(data, qty)
        results = {"key":api_key, "secret":api_secret,"telegram_id":telegram_id }
        return results
    except Exception as e:
        print("The position Error", str(e))
        position_resp=f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT Order Failed\nError:{str(e)}"
        sendMessage(telegram_id, position_resp )
        return None

        

       

    
def user_counter():
  pass
  sub = redsub.pubsub()
  sub.subscribe('smart-signals-kucoin-order-2')
  for signal_data in sub.listen():
    #   print("signal data", signal_data)
      if signal_data is not None and isinstance(signal_data, dict):

        try:
            order_data = json.loads(signal_data['data'])
            # print("orser data", order_data)
            data= {"position":{
                    "symbol":order_data['symbol'][:-1].upper(),
                    "side":order_data["side"].upper(),
                    "quantity":None,#to be inserted for a specific user while send order
                    "type":order_data["type"].upper()
                    }}

            print("position data", data)
            # data = orderDataTemplateProcessor(order_data) #missing parts in amount, takeprofit amounts and stop loss amounts
            symbolredis =data['position']['symbol']
            # print(symbolredis)
            # print(data)
            # # priceredis = str(data['position']['price'])+"-"+str(data['position']['side'])
            # priceredis = str(data['position']['price'])
            # print("price redis key", priceredis)

            print("The symbol redis", symbolredis)
            if signal_data is not False:
                with app.app_context():
                    users = getAllUserConfigs()
                    print(users)
                if users ==[]:#if no data
                    pass
                else:

                    all_results =[]
                    for user in users:
                        # if user.telegram_id ==str(1499548874):
                        api_key =user.key
                        api_secret=user.secret
                        leverage=20
                        amount=convert_usdt_to_base_asset(symbolredis, user.amount, leverage)
                        if data['position']['side']=='XL' or data['position']['side']=='XS':
                            print("closing the symbol orders first")
                            # response =cancelAllPositionBySymbol(api_key, api_secret,symbolredis)
                            # if response:
                            #     sendMessage(user.telegram_id, f"All orders and positions for {symbolredis} closed successfully.")
                            # else:
                            #     sendMessage(user.telegram_id, f"You have no open positions for {symbolredis}")

                        else:
                            print("closing the symbol orders first")
                            cancelAllPositionBySymbol(api_key, api_secret,symbolredis)
                            print("Sending the order to binance")
                            resp =send_orders(api_key,api_secret,amount, data, user.telegram_id)
                            if resp is not None:
                                all_results.append(resp)
                    
                    print(all_results)

                    
        except Exception as e:
          print("error found", str(e))

while True:
  user_counter() 
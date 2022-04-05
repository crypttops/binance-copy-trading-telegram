import json
from operator import pos
import pickle
from pydoc_data.topics import topics
import queue
from typing import Dict
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
def orderDataTemplateProcessor(data:Dict):
    orders ={}
    position = data["position"]
    pair = data["pair"].upper().replace("USDT_", "")
    amount =data["position"]["units"]["value"]
    volume_per_tp = data["take_profit"]["steps"][0]["volume"]
    
    position_side =data["position"]["type"]
    if position_side=="sell":
        data["position"]["type"]="buy"
    elif position_side =="buy":
        data["position"]["type"]="sell"

    position_side =data["position"]["type"]
    if position_side == "sell":
        tp_side = "buy"
    if position_side =="buy":
        tp_side = "sell"
    position_data={
                    "symbol":pair.upper(),
                    "side":position["type"].upper(),
                    "quantity":None,#to be inserted for a specific user while send order
                    "type":position["order_type"].upper(),
                    # "type":"MARKET",
                    "price":position["price"]['value']
                    }
    close_position_data={
        "symbol":pair.upper(),
        "side":tp_side.upper(),
        "quantity":None,#to be inserted for a specific user while send order
        "type":'MARKET',
        
    }
    #updating position order 
    orders.update({"position":position_data, 'close_position_data':close_position_data})

    take_profits = data["take_profit"]["steps"]
    tp_orders =[]
    for tp in take_profits:
        tp_order={
        "symbol":pair,
        "side":tp_side.upper() ,
        "quantity":None,#to be inserted for a specific user while send order
        "type":tp["order_type"].upper(),
        "price":tp["price"]["value"],
        "reduceOnly":"true"

        }
        tp_orders.append(tp_order)

    orders.update({"take_profit_orders":tp_orders})

    #updating stoploss order
    stop_loss = data["stop_loss"]
    stop_loss_order = {"symbol":pair.upper(),"side":tp_side.upper(), "quantity":None, "type":stop_loss["order_type"].upper(), "price":stop_loss["price"]["value"]}
    orders.update({"stop_loss_order":stop_loss_order})
    return orders




def tps_n_sls(data, qty):
    # placing the takeprofits and stoploss orders

    tp_length = len(data["take_profit_orders"])

    for tp in range(tp_length):
        data['take_profit_orders'][tp]["quantity"]=float(qty)/tp_length
    data["stop_loss_order"]["quantity"]=float(qty)
    return data


def send_orders(api_key, api_secret, qty, data, telegram_id):

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
        position_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT placed at {position_params['price']}"
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
  sub.subscribe('smart-signals-kucoin-order')
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
            # data = orderDataTemplateProcessor(order_data) #missing parts in amount, takeprofit amounts and stop loss amounts
            symbolredis =data['position']['symbol']
            # print(symbolredis)
            # print(data)
            # # priceredis = str(data['position']['price'])+"-"+str(data['position']['side'])
            # priceredis = str(data['position']['price'])
            # print("price redis key", priceredis)


            if signal_data is not False:
                with app.app_context():
                    users = getAllUserConfigs()
                    print(users)
                if users ==[]:#if no data
                    pass
                else:
                    threads =[]

                    # for user in users:
                    #     api_key =user.key
                    #     api_secret=user.secret
                    #     amount=user.amount
                    #     t1 = threading.Thread(target=send_orders, args=(api_key,api_secret,amount, data, user.telegram_id))
                    #     threads.append(t1)
                    # print("threads:", threads)
                    # for thread in threads:
                    #     thread.start()

                    # all_results =[]
                    # for thread in threads:
                    #     thread.join()
                    #     my_data = my_queue.get()
                    #     all_results.append(my_data)
                    #     print("my_Data",my_data)

                    # print("Done!")
                    # print(all_results)
                    # red.set(str(all_results[0]['position']['price']), pickle.dumps(all_results))


                    # without threads implementation

                    # check where is the price of the position from the entry
                    # last_price = get_last_price_ticker(symbolredis)
                    # if float(last_price)>=float(data['position']['price']):
                    #     price_state ="ETOP"#above the entry
                    # else:
                    #     price_state="ELOW"#below the entry

                    all_results =[]
                    for user in users:
                        # if user.telegram_id ==str(1499548874):
                        api_key =user.key
                        api_secret=user.secret
                        leverage=20
                        amount=convert_usdt_to_base_asset(symbolredis, user.amount, leverage)
                        resp =send_orders(api_key,api_secret,amount, data, user.telegram_id)
                        if resp is not None:
                            all_results.append(resp)
                    
                    print(all_results)
                    #save the orders to redis and start monitoring the price changes immediately
                    # records = {
                    #     "position_close_data":data['close_position_data'],
                    #     "users":all_results
                    # }
                    # red.set(str(priceredis), pickle.dumps(records))
                    # # task_instance = startPriceStreams.apply_async(args=(symbolredis, priceredis,price_state))
                    # # print(task_instance)
                    # print("Cache update successifully")


                    
        except Exception as e:
          print("error found", str(e))

while True:
  user_counter() 
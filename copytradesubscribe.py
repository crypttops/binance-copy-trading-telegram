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
    if position_side == "sell":
        tp_side = "buy"
    if position_side =="buy":
        tp_side = "sell"
    position_data={
                    "symbol":pair.upper(),
                    "side":position["type"].upper(),
                    "quantity":None,#to be inserted for a specific user while send order
                    "type":position["order_type"].upper(),
                    "price":position["price"]['value']
                    }
    #updating position order 
    orders.update({"position":position_data})

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




my_queue = queue.Queue()

def tps_n_sls(data, qty):
    # placing the takeprofits and stoploss orders

    tp_length = len(data["take_profit_orders"])

    for tp in range(tp_length):
        data['take_profit_orders'][tp]["quantity"]=float(qty)/tp_length
    data["stop_loss_order"]["quantity"]=float(qty)
    return data

def storeInQueue(f):
  def wrapper(*args):
    my_queue.put(f(*args))
  return wrapper


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
    


    
        # responses=[]
        
        # tp_params = data["take_profit_orders"]
        # print("The takeprofits", tp_params)
        # tp_resp =''
        # count=1
        # for tp_param in tp_params:
        #     print("The type of type object", type(tp_param))
        #     try:
        #         print("tp_param to send order", tp_param)
        #         resp = client.sendOrder(tp_param)
        #         bot_resp = f"[Binance Futures USDT-M]\n{tp_param['symbol']}/USDT TakeProfit {tp_param['side'].lower()} order placed @{tp_param['price']}\n\n"
        #     except Exception as e:
        #         print("The takeprofit error", str(e))
        #         bot_resp = f"[Binance Futures USDT-M]\n{tp_param['symbol']}/USDT TakeProfit {tp_param['side'].lower()} @{tp_param['price']}Order Failed\nError:{str(e)}\n\n"
        #     tp_resp+=bot_resp
        # sendMessage(telegram_id, tp_resp)

        # #send stop loss orders
        # sl_params = data["stop_loss_order"]
        # try:
        #     resp = client.sendOrder(sl_params)
        #     sl_resp = f"[Binance Futures USDT-M]\n{sl_params['symbol']}/USDT StopLoss {sl_params['side'].lower()} order placed @{sl_params['price']}\n\n"

        # except Exception as e:
        #     print("The sl error", str(e))
        #     sl_resp = f"[Binance Futures USDT-M]\n{sl_params['symbol']}/USDT StopLoss {sl_params['side'].lower()} @{sl_params['price']}Order Failed\nError:{str(e)}\n\n"
       
        # sendMessage(telegram_id, sl_resp)


    
    # send the position order
    position_params = data["position"]
    print("the data, ", position_params)
    try:
        resp = client.sendOrder(position_params)
        print("the response",resp)
        position_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT placed at {position_params['price']}"
        sendMessage(telegram_id, position_resp )
        results = tps_n_sls(data, qty)
        results.update({"key":api_key, "secret":api_secret,"telegram_id":telegram_id })
        return results
    except Exception as e:
        print("The position Error", str(e))
        position_resp=f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT Order Failed\nError:{str(e)}"
        sendMessage(telegram_id, position_resp )
        return None

        

       

    
def user_counter():
  pass
  sub = redsub.pubsub()
  sub.subscribe('smart-signals')
  for signal_data in sub.listen():
      if signal_data is not None and isinstance(signal_data, dict):
        try:
            order_data = json.loads(signal_data['data'])
            data = orderDataTemplateProcessor(order_data) #missing parts in amount, takeprofit amounts and stop loss amounts
            symbolredis =data['position']['symbol']
            priceredis = str(data['position']['price'])+"-"+str(data['position']['side'])


            if signal_data is not False:
                with app.app_context():
                    users = getAllUserConfigs()
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
                    last_price = get_last_price_ticker(symbolredis)
                    if float(last_price)>=float(data['position']['price']):
                        price_state ="ETOP"#above the entry
                    else:
                        price_state="ELOW"#below the entry

                    all_results =[]
                    for user in users:
                        api_key =user.key
                        api_secret=user.secret
                        leverage=20
                        amount=convert_usdt_to_base_asset(symbolredis, user.amount, leverage)
                        resp =send_orders(api_key,api_secret,amount, data, user.telegram_id)
                        if resp is not None:
                            all_results.append(resp)
                    print(all_results)
                    #save the orders to redis and start monitoring the price changes immediately

                    red.set(str(priceredis), pickle.dumps(all_results))
                    task_instance = startPriceStreams.apply_async(args=(symbolredis, priceredis,price_state))
                    print(task_instance)


                    
        except Exception as e:
          print("error found", str(e))

while True:
  user_counter()
import json
from operator import pos
import pickle
from pydoc_data.topics import topics
import queue
from tracemalloc import stop
from typing import Dict
from backend.operations.binance import cancelAllPositionBySymbol, checkIfPositionExists
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


def CheckOpenPositions(client):
    position = client.checkPositionInfo()
    # print(position)
    if not position:
        return "You have no open positions"
    processed = []
    for pos in position:
        if float(pos['unRealizedProfit']) != float("0.00000000"):
            print("positon response", pos)
            side = "SELL" if float(pos['positionAmt']) < 0 else "BUY"
            data = {
                "symbol": pos["symbol"],
                "positionSide": pos["positionSide"],
                "unRealizedProfit": pos["unRealizedProfit"],
                "liquidationPrice": pos['liquidationPrice'],
                "positionAmt": pos['positionAmt'],
                "side": side
            }
            processed.append(data)

    # if processed == []:
    #     return "You have no open positions"

    return {
        "status": "OK",
        "result": processed
    }, 200

def createSlTpOrder(client, orderDetails):
    resp = CheckOpenPositions(client)
    print("postiton sresp", resp)
    for res in resp[0]['result']:
        if res['symbol'] == orderDetails['symbol']:
            orderDetails['quantity'] = client.round_decimals_down(
                abs(float(res['positionAmt'])), client.qtyPrecision)
            orderDetails['stopPrice'] = client.round_decimals_down(orderDetails['stopPrice'], client.pricePrecision)

            try:
                resp = client.futures_create_order(
                    **orderDetails)
                print(resp)
                return resp, 200
            except Exception as e:
                resp = {
                    "status": "fail",
                    "result": str(e),
                    "message": "error occured. Check parameters"
                }
                return resp, 400
        break
    return None

        
def tPSlHandler(params):
    # Preparing the sl

    if "takeProfit" in params:
        tp =params["takeProfit"]
    else:
        tp=""
    if "stopLoss" in params: 
        sl = params["stopLoss"]
    else:
        sl =""
    origparams = params.copy()
    bot_message = "\n\n"
    stop_side="buy" if params['side']=='sell' else "sell"

    if tp !="":
        last_price = get_last_price_ticker(params["symbol"])
        
        # Calculating the tp with leverage
        tp = float(tp)/float(params['leverage'])

        if origparams['side'] == "buy":
            tp_price = ((100 + float(tp))/100)*float(last_price) 
            tp_payload ={"symbol": params['symbol'],
            "side": stop_side.upper(),
            "type": "TAKE_PROFIT_MARKET",
            "quantity": None,
            "stopPrice": tp_price,
            'timeInForce': 'GTC',
            'reduceOnly': 'true'}
            
            params.update({"takeProfit":tp_payload})
        elif origparams["side"] =="sell":
            tp_price = ((100 - float(tp))/100)*float(last_price) 
            tp_payload ={"symbol": params['symbol'],
            "side": stop_side.upper(),
            "type": "TAKE_PROFIT_MARKET",
            "quantity": None,
            "stopPrice": tp_price,
            'timeInForce': 'GTC',
            'reduceOnly': 'true'}
            
            params.update({"takeProfit":tp_payload})
        
    if sl !="":
        #calculate the percentage of the price
        last_price = get_last_price_ticker(params["symbol"])

        sl = float(sl)/float(params['leverage'])
        
        if origparams['side'] == "buy":
            sl_price = ((100 - float(sl))/100)*float(last_price) 
            sl_payload ={"symbol": params['symbol'],
            "side": stop_side.upper(),
            "type": "STOP_MARKET",
            "quantity": None,
            "stopPrice": sl_price,
            'timeInForce': 'GTC',
            'reduceOnly': 'true'}
            
            params.update({"stopLoss":sl_payload})
        elif origparams["side"] =="sell":
            sl_price = ((100 + float(sl))/100)*float(last_price) 
            sl_payload ={"symbol": params['symbol'],
                "side": stop_side.upper(),
                "type": "STOP_MARKET",
                "quantity": None,
                "stopPrice": sl_price,
                'timeInForce': 'GTC',
                'reduceOnly': 'true'}
            
            params.update({"stopLoss":sl_payload})
    return params

        





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
        if checkIfPositionExists(client, trade_symbol):
            sendMessage(telegram_id, f"You already have a position for symbol {trade_symbol}" )

        resp = client.sendOrder(position_params)
        print("the response",resp)
        position_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT placed successfully"
        sendMessage(telegram_id, position_resp )

        # results = tps_n_sls(data, qty)
        if 'takeProfit' in data:
            tpresp= createSlTpOrder(client, data['takeProfit'])
            print("tp_resp", tpresp)
        if 'stopLoss' in data:
            slresp = createSlTpOrder(client, data['stopLoss'])
            print("sl_resp", slresp)

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
      print("signal data", signal_data)
      if signal_data is not None and isinstance(signal_data, dict):
        
        try:
            order_data = json.loads(signal_data['data'])
            if order_data['channel_id'] == 1093054762:
                #handle the symbol
                print("intial", order_data)
                order_data['symbol'] = order_data['symbol'][:-1].upper()
                print("order_data", order_data)
                # print("orser data", order_data)
                data = tPSlHandler(order_data)
                data.update({"position":{
                        "symbol":order_data['symbol'],
                        "side":order_data["side"].upper(),
                        "quantity":None,#to be inserted for a specific user while send order
                        "type":order_data["type"].upper()
                        }
                        
                        })


                print("data", data)
                # data = orderDataTemplateProcessor(order_data) #missing parts in amount, takeprofit amounts and stop loss amounts
                symbolredis =data['position']['symbol']

                # Preparing the sl
                print("The symbol redis", symbolredis)
                if signal_data is not False:
                    with app.app_context():
                        users = getAllUserConfigs()
                        print("The users", users)
                    if users ==[]:#if no data
                        pass
                    else:

                        all_results =[]
                        for user in users:

                            # if user.telegram_id ==str(1093054762):
                                
                            api_key =user.key
                            api_secret=user.secret
                            leverage=20
                            amount=convert_usdt_to_base_asset(symbolredis, 1, leverage)
                            if data['position']['side']=='XL' or data['position']['side']=='XS':
                                print("closing the symbol orders first")
                                # response =cancelAllPositionBySymbol(api_key, api_secret,symbolredis)
                                # if response:
                                #     sendMessage(user.telegram_id, f"All orders and positions for {symbolredis} closed successfully.")
                                # else:
                                #     sendMessage(user.telegram_id, f"You have no open positions for {symbolredis}")

                            else:
                                # print("closing the symbol orders first")
                                # cancelAllPositionBySymbol(api_key, api_secret,symbolredis)
                                # print("Sending the order to binance")
                                resp =send_orders(api_key,api_secret,amount, data, user.telegram_id)
                                if resp is not None:
                                    all_results.append(resp)
                    
                        print(all_results)

                    
        except Exception as e:
          print("error found", str(e))

while True:
  user_counter() 
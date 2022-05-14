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
from backend.operations.pnlcalc import getTpEntryPrice
from backend.operations.price import convert_usdt_to_base_asset, get_last_price_ticker

from config import Config
from tasks import startPriceStreams
from backend.utils import logging
red = redis.from_url(Config.REDIS_URL)
redsub= redis.from_url(Config.REDES_SUB_URL)
bot_token = Config.BOT_TOKEN

logger = logging.GetLogger(__name__)
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
        
    orderDetails['stopPrice'] = client.round_decimals_down(orderDetails['stopPrice'], client.pricePrecision)
    orderDetails['quantity'] =client.round_decimals_down(orderDetails["quantity"], client.qtyPrecision)

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
    leverage=20 if params['leverage']== None else params['leverage']
    bot_message = "\n\n"
    stop_side="buy" if params['side']=='sell' else "sell"

    if tp !="":
        last_price = get_last_price_ticker(params["symbol"])
        # Calculating the tp with leverage
        tp = float(tp)
        leverage = 20
        entry_price = last_price if 'price' not in origparams else origparams['price'] 
        
        if origparams['side'] == "buy":
            if "signal" in origparams:
               
                # tp_price = params["takeProfit"] 
                # tp_price = ((100 + float(tp))/100)*float(last_price)
                tp_price = getTpEntryPrice(origparams['side'],entry_price, tp,leverage)
            else:
                # tp_price = ((100 + float(tp))/100)*float(last_price)  
                tp_price = getTpEntryPrice(origparams['side'],entry_price, tp,leverage) 

            tp_payload ={"symbol": params['symbol'],
            "side": stop_side.upper(),
            "type": "TAKE_PROFIT_MARKET",
            "quantity": None,
            "stopPrice": tp_price,
            'timeInForce': 'GTC',
            'reduceOnly': 'true'}
            
            params.update({"takeProfit":tp_payload})
        elif origparams["side"] =="sell":
            if "signal" in origparams:
                # tp_price = params["takeProfit"]
                tp_price = getTpEntryPrice(origparams['side'],entry_price, tp,leverage)   
            else:
                # tp_price = ((100 - float(tp))/100)*float(last_price) 
                tp_price = getTpEntryPrice(origparams['side'],entry_price, tp,leverage) 

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
    
        sl = float(sl)/float(leverage)
        
        if origparams['side'] == "buy":
            if "signal" in origparams:
                sl_price = params["stopLoss"]
            else:
                # sl_price = ((100 - float(sl))/100)*float(last_price) 
                sl_price = getTpEntryPrice(origparams['side'],entry_price, (sl*-1),leverage) 

            sl_payload ={"symbol": params['symbol'],
            "side": stop_side.upper(),
            "type": "STOP_MARKET",
            "quantity": None,
            "stopPrice": sl_price,
            'timeInForce': 'GTC',
            'reduceOnly': 'true'}
            
            params.update({"stopLoss":sl_payload})
        elif origparams["side"] =="sell":
            if "signal" in origparams:
                sl_price = params["stopLoss"]
            else:
                # sl_price = ((100 + float(sl))/100)*float(last_price)
                sl_price = getTpEntryPrice(origparams['side'],entry_price, (sl*-1),leverage) 

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
   
    """
    #Order template
    """
    trade_symbol= data['position']['symbol']
    client = BinanceFuturesOps(api_key=api_key, api_secret=api_secret, trade_symbol=trade_symbol)
   
    data["position"]["quantity"]=float(qty)
    data["takeProfit"]["quantity"]=float(qty)
    data["stopLoss"]["quantity"]=float(qty)
    print("Data after updating the quantiy", data)

    logger.info(f"{telegram_id}-Order payload- {data}")    
    # send the position order
    position_params = data["position"]
    try:
        if checkIfPositionExists(client, trade_symbol):
            sendMessage(telegram_id, f"You already have a position for symbol {trade_symbol}" )
            logger.info(f"{telegram_id}  You already have a position for symbol {trade_symbol}")
            return 1

        resp = client.sendOrder(position_params)
        position_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT Order placed successfully"
        logger.info(f"{telegram_id} - {position_resp}")
        sendMessage(telegram_id, position_resp )

        # results = tps_n_sls(data, qty)
        if 'takeProfit' in data:
            tpresp, status = createSlTpOrder(client, data['takeProfit'])

            if 'orderId' in tpresp:
                tp_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT Takeprofit Order placed successfully"
                sendMessage(telegram_id, tp_resp )
                logger.info(f"{telegram_id} - {tp_resp}")
            else:
                tp_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT Takeprofit Order failed"
                sendMessage(telegram_id, tp_resp )
                logger.error({telegram_id} - {str(tpresp)})

        if 'stopLoss' in data:
            slresp, status = createSlTpOrder(client, data['stopLoss'])
            if 'orderId' in slresp:
                sl_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT StopLoss Order placed successfully"
                sendMessage(telegram_id, sl_resp )
                logger.info(f"{telegram_id} - {sl_resp}")

            else:
                sl_resp = f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT StopLoss Order failed"
                sendMessage(telegram_id, sl_resp )
                logger.error(f"{telegram_id} - {str(slresp)}")
        return "Done"
    except Exception as e:
        logger.error(f"{telegram_id} - {str(e)}")
        position_resp=f"[Binance Futures USDT-M]\n{position_params['symbol']}/USDT Order Failed\nError:{str(e)}"
        sendMessage(telegram_id, position_resp )
        return None

        

       

    
def user_counter():
  pass
  sub = redsub.pubsub()
  sub.subscribe('smart-signals-kucoin-order-3')
  for signal_data in sub.listen():
      if signal_data is not None and isinstance(signal_data, dict):
        
        try:
            order_data = json.loads(signal_data['data'])
          
            #handle the symbol
            order_data['symbol'] = order_data['symbol'][:-1].upper()
            # print("orser data", order_data)
            data = tPSlHandler(order_data)
            logger.info(f"TP SL Template data {data}")
            if order_data["type"].upper() =="LIMIT":
                data.update({"position":{
                        "symbol":order_data['symbol'],
                        "side":order_data["side"].upper(),
                        "quantity":None,#to be inserted for a specific user while send order
                        "type":order_data["type"].upper(),
                        "price":order_data["price"] 
                        }
                        
                        })
            else:
                 data.update({"position":{
                        "symbol":order_data['symbol'],
                        "side":order_data["side"].upper(),
                        "quantity":None,#to be inserted for a specific user while send order
                        "type":order_data["type"].upper(),
                        }
                        
                        })

            logger.info(f"Template orders data {data}")
            # data = orderDataTemplateProcessor(order_data) #missing parts in amount, takeprofit amounts and stop loss amounts
            symbolredis =data['position']['symbol']

            # Preparing the sl
            if signal_data is not False:
                with app.app_context():
                    users = getAllUserConfigs()

                if users ==[]:#if no data
                    pass
                else:

                    all_results =[]
                    for user in users:

                        # if user.telegram_id ==str(1093054762):
                            
                        api_key =user.key
                        api_secret=user.secret
                        leverage=user.leverage
                        amount=convert_usdt_to_base_asset(symbolredis,user.amount, leverage)
                        if data['position']['side']=='XL' or data['position']['side']=='XS':
                            pass
                            # response =cancelAllPositionBySymbol(api_key, api_secret,symbolredis)
                            # if response:
                            #     sendMessage(user.telegram_id, f"All orders and positions for {symbolredis} closed successfully.")
                            # else:
                            #     sendMessage(user.telegram_id, f"You have no open positions for {symbolredis}")

                        else:
                            # print("closing the symbol orders first")
                            # cancelAllPositionBySymbol(api_key, api_secret,symbolredis)
                            # print("Sending the order to binance")
                            
                            send_orders(api_key,api_secret,amount, data, user.telegram_id)
                            
                
        except Exception as e:
          logger.error(str(e))

while True:
  user_counter() 
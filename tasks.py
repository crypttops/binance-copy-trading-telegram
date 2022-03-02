import pickle
from celery import Celery
import redis
from backend.operations.binance_futures import BinanceFuturesOps
from backend.operations.bot import sendMessage
from backend.utils.binance.streams import ThreadedWebsocketManager
from config import Config
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL,
                backend=Config.CELERY_BROKER_URL)

red = redis.from_url(Config.REDIS_URL)

@celery.task()
def startPriceStreams( symbol, rediskeyname):
    # Update the bookTicker price of the trading symbols
    print("rediskeyname", rediskeyname)
    prices_api_key = "02eTTLVw9T6g3oEmelloLP3IGt8QlCoCOKvdWshpKU1KWOQ7sDIm2xrDOPe3X9S6 "
    prices_api_secret = "MjP6qfoCnLX8KeIFAzW0KyE3LL96xlbbTYI962pWtyaES4SBIWiJXBJ1S3uMwoS8"
    twm = ThreadedWebsocketManager(api_key=prices_api_key, api_secret=prices_api_secret)

    def handle_socket_message(price_data):
        print(price_data)

        price = price_data['data']['b']
        if float(price) >=float(rediskeyname):
            print("Stop now")
            twm.stop()
            print("target reached send takeprofits now")
            details = pickle.loads(red.get(rediskeyname))
            print("The are the details to use to place the orders", details)
            for user_order_details in details:
                api_key =user_order_details['key']
                api_secret = user_order_details['secret']
                client = BinanceFuturesOps(api_key=api_key, api_secret=api_secret, trade_symbol=user_order_details['position']['symbol'])
                telegram_id = user_order_details['telegram_id']
                tp_params = user_order_details['take_profit_orders']
                tp_resp =''
                for tp_param in tp_params:
                    print("The type of type object", type(tp_param))
                    try:
                        print("tp_param to send order", tp_param)
                        resp = client.sendOrder(tp_param)
                        bot_resp = f"[Binance Futures USDT-M]\n{tp_param['symbol']}/USDT TakeProfit {tp_param['side'].lower()} order placed @{tp_param['price']}\n\n"
                    except Exception as e:
                        print("The takeprofit error", str(e))
                        bot_resp = f"[Binance Futures USDT-M]\n{tp_param['symbol']}/USDT TakeProfit {tp_param['side'].lower()} @{tp_param['price']}Order Failed\nError:{str(e)}\n\n"
                    tp_resp+=bot_resp
                sendMessage(telegram_id, tp_resp)

                #send stop loss orders
                sl_params = user_order_details["stop_loss_order"]
                try:
                    resp = client.sendOrder(sl_params)
                    sl_resp = f"[Binance Futures USDT-M]\n{sl_params['symbol']}/USDT StopLoss {sl_params['side'].lower()} order placed @{sl_params['price']}\n\n"

                except Exception as e:
                    print("The sl error", str(e))
                    sl_resp = f"[Binance Futures USDT-M]\n{sl_params['symbol']}/USDT StopLoss {sl_params['side'].lower()} @{sl_params['price']}Order Failed\nError:{str(e)}\n\n"
            
                sendMessage(telegram_id, sl_resp)



    twm.start()

    twm.start_symbol_ticker_futures_socket(
        callback=handle_socket_message, symbol=symbol)
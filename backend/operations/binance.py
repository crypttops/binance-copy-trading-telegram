import json
from backend.models.botconfig import BotConfigsModel
from backend.operations.binance_futures import BinanceFuturesOps
from db import db

def getAllOpenOrders(telegram_id):
    user = db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).first()
    client = BinanceFuturesOps(api_key=user.key, api_secret=user.secret, trade_symbol="BTCUSDT")
    open_orders = client.checkAllOPenOrders()
    if not open_orders:
        return "You have no open orders"
    processed =[]
    for order in open_orders:
        data = {
                "orderId":order["orderId"],
                "symbol":order["symbol"],
                "side":order["side"],
                "reduceOnly":order["reduceOnly"]  
              }
        processed.append(data)
    # print(json.dumps(processed, indent=4))
    return json.dumps(processed, indent=4)

def getAllOpenPositions(telegram_id):
    user = db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).first()
    client = BinanceFuturesOps(api_key=user.key, api_secret=user.secret, trade_symbol="BTCUSDT")
    position = client.checkPositionInfo()
    # print(position)
    if not position:
        return "You have no open positions"
    processed =[]
    for pos in position:
        if float(pos['unRealizedProfit']) != float("0.00000000"):
            data={
                "symbol":pos["symbol"],
                "positionSide":pos["positionSide"],
                "unRealizedProfit":pos["unRealizedProfit"],
                "liquidationPrice":pos['liquidationPrice']
            }
            processed.append(data)

    
    if processed == []:
        return "You have no open positions"

    return json.dumps(processed, indent=4)

def cancelAllPositionBySymbol(api_key, api_secret, symbol):
    client = BinanceFuturesOps(api_key=api_key, api_secret=api_secret, trade_symbol=symbol,)
    paramsCancel = {
                
                "symbol":symbol[-1],
                }
    cancel_ret = client.futures_cancel_all_open_orders(**paramsCancel)
    position = client.checkPositionInfo()
    if not position:
        return None
    processed =[]
    for pos in position:
        if float(pos['unRealizedProfit']) != float("0.00000000"):

            side = "SELL" if float(pos['positionAmt']) < 0 else "BUY"

            closeSide= "SELL" if side=='BUY' else "SELL"
            position_cancel_params={'symbol': symbol, 'type': 'MARKET', 'side':closeSide, 'quantity':float(pos['positionAmt'])}
            cancel_ret = client.sendOrder(position_cancel_params)
            print(cancel_ret)
            processed.append(1)
    
    if processed == []:
        return False

    return True
def checkIfPositionExists(client, symbol):
    position = client.checkPositionInfo()
    if not position:
        return False
    processed =[]
    for pos in position:
        if float(pos['unRealizedProfit']) != float("0.00000000"):
            if pos['symbol'] == symbol:
                processed.append(1)
                break
    
    if processed == []:
        return False

    return True

def getAllOpenOrderSymbol(telegram_id):
    user = db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).first()
    client = BinanceFuturesOps(api_key=user.key, api_secret=user.secret, trade_symbol="BTCUSDT")
    open_orders = client.checkAllOPenOrders()
    if not open_orders:
        return "You have no open orders"
    processed =[]
    for order in open_orders:
        data = {
                "symbol":order["symbol"],  
              }
        processed.append(data)
    # print(json.dumps(processed, indent=4))
    return json.dumps(processed, indent=4)

    


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

    


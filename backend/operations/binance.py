from backend.models.botconfig import BotConfigsModel
from backend.operations.binance_futures import BinanceFuturesOps
from db import db

def getAllOpenPositions(telegram_id):
    user = db.session.query(BotConfigsModel).filter_by(telegram_id=telegram_id).first()
    client = BinanceFuturesOps(api_key=user.key, api_secret=user.secret, trade_symbol="BTCUSDT")
    open_orders = client.checkAllOPenOrders()
    if not open_orders:
        return "You have no open positions"
        
    return open_orders

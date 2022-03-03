from backend.utils.binance.clientOriginal import Client as BinanceClient
import math


class BinanceFuturesOps(BinanceClient):
    def __init__(self, api_key=None, api_secret=None, requests_params=None, tld='com', trade_symbol=None):
        super().__init__(api_key=None, api_secret=None, requests_params=None, tld='com')

        self.API_URL = self.API_URL.format(tld)
        self.MARGIN_API_URL = self.MARGIN_API_URL.format(tld)
        self.WEBSITE_URL = self.WEBSITE_URL.format(tld)
        self.FUTURES_URL = self.FUTURES_URL.format(tld)

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params
        self.response = None

        # init DNS and SSL cert
        self.ping()
        # authentication stored in is_authentic
        self.is_authentic = self.authenticateKeys()
        self.trade_symbol = trade_symbol

        self.base_asset = self.symbolInfo()["baseAsset"]
        self.quote_asset = self.symbolInfo()["quoteAsset"]

        self.pricePrecision = self.getAssetPrecision()["pricePrecision"]
        self.qtyPrecision = self.getAssetPrecision()["qtyPrecision"]

        self.lastPrice = self.getLastPrice()

        self.timeInForce = 'GTC'

    def symbolInfo(self):
        exchange_info = self.get_exchange_info()
        for exchange in exchange_info['symbols']:
            if exchange["symbol"] == self.trade_symbol:
                base_asset = exchange["baseAsset"]
                quote_asset = exchange["quoteAsset"]

                return {"baseAsset": base_asset, "quoteAsset": quote_asset}
                break

    def precisionValueCalc(self, x):
        max_digits = 14
        int_part = int(abs(x))
        magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
        if magnitude >= max_digits:
            return (magnitude, 0)
        frac_part = abs(x) - int_part
        multiplier = 10 ** (max_digits - magnitude)
        frac_digits = multiplier + int(multiplier * frac_part + 0.5)
        while frac_digits % 10 == 0:
            frac_digits /= 10
        count = int(math.log10(frac_digits))
        return count

    def round_decimals_down(self, number: float, decimals: int = 2):
        """
        Returns a value rounded down to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)

        factor = 10 ** decimals
        return math.floor(number * factor) / factor

    def authenticateKeys(self):
        # authenticating the api_keys
        try:
            params = {'symbol': 'BTCUSDT', 'recvWindow': 60000}
            self.futures_get_open_orders(**params)
            return True
        except Exception as e:
            return {"message": e.message, "status": e.status_code}

    # check open orders for a specific symbol
    def checkOpenOrdersForSymbol(self):
        params = {'symbol': self.trade_symbol}

        if self.is_authentic == True:
            res = self.futures_get_open_orders(**params)
            if res == None or res == []:
                return False
            else:
                return res
        else:
            return self.is_authentic

    def checkAllOPenOrders(self):
        # params={'symbol':self.trade_symbol}

        if self.is_authentic == True:
            res = self.futures_get_open_orders()
            if res == None or res == []:
                return False
            else:
                return res
        else:
            return self.is_authentic

    def checkAllOrders(self):
        params = {'symbol': self.trade_symbol}

        if self.is_authentic == True:
            res = self.futures_get_all_orders(**params)
            if res == None or res == []:
                return False
            else:
                return res
        else:
            return self.is_authentic

    def checkWalletBalance(self, params):
        # params= { 'asset':'BTC'}
        
        if self.is_authentic == True:
            if params['asset'] == self.quote_asset:
                balances = self.futures_account_balance()
                res = next(item["balance"] for item in balances if item["asset"] == self.quote_asset)
                return res

            if params['asset'] == self.base_asset:
                balances = self.futures_account_balance()
                res = next(item["balance"] for item in balances if item["asset"] == self.base_asset)
                return res
        else:
            return self.is_authentic

    def getLastPrice(self):
        # params= { 'symbol':'BTC'}
        params = {'symbol': self.trade_symbol}
        if self.is_authentic == True:
            try:
                res = self.futures_symbol_ticker(**params)
                return float(res['price'])
            except Exception as e:
                return e
        else:
            return self.is_authentic

    def getAssetPrecision(self):
        assetSymbol = self.trade_symbol
        info = self.futures_exchange_info()

        pricePrecision = 0
        quantityPrecision = 0

        for i in range(len(info['symbols'])):
            if assetSymbol == info['symbols'][i]['symbol']:
                pricePrecision = int(info['symbols'][i]['pricePrecision'])
                quantityPrecision = int(info['symbols'][i]['quantityPrecision'])

        return {"pricePrecision": pricePrecision, "qtyPrecision": quantityPrecision}

    def getOrderQuantity(self, walletBalance, lastPrice, leverage):
        ticks = {}
        for filt in self.get_symbol_info(self.trade_symbol)['filters']:
            if filt['filterType'] == 'LOT_SIZE':
                ticks[self.quote_asset] = filt['stepSize'].find('1') - 2
                break
        
        orderQuantity = ((math.floor(float(walletBalance)) *
                          10**ticks[self.quote_asset] / lastPrice)/float(10**ticks[self.quote_asset])) * leverage

        return self.round_decimals_down(orderQuantity, self.qtyPrecision)

    def setLeverage(self, params):
        # {"leverage":10, "symbol":self.trade_symbol }
        leverage = self.futures_change_leverage(**params)
        return leverage

    def getTakeProfit(self, percentVal):
        takeProfit = self.lastPrice + ((percentVal / 100) * self.lastPrice)
        return (self.round_decimals_down(takeProfit, self.pricePrecision))

    def getLimitPrice(self, percentVal):
        limitPrice = round(
            self.lastPrice - (float(percentVal)/100) * self.lastPrice, 8)
        return float(self.round_decimals_down(limitPrice, self.pricePrecision))

    def LimitOrder(self, params):
        """Process the values of Limit order"""
        print("the data klnkls", params)
        price = params["price"]
        quantity =self.round_decimals_down(params["quantity"], self.qtyPrecision)
        # quantity = params["quantity"]
        return {"timeInForce": self.timeInForce, "price": price, "quantity": quantity}

    def takeProfitOrder(self, params):
        """Process the values of take profit Limit order"""
        stopPrice = 0
        if params["side"] == 'BUY':
            stopPrice = self.getLimitPrice(params['takeProfit'])
        if params["side"] == "SELL":
            stopPrice = self.getTakeProfit(params['takeProfit'])

        price = self.getLastPrice()
        quantity = params["quantity"]

        return {"stopPrice": stopPrice, "price": price, "quantity": quantity}
    
    def StopOrder(self, params):
        """Process the values of take profit Limit order"""
        stopPrice = 0
        if params["side"] == 'BUY':
            stopPrice = self.getTakeProfit(params['takeProfit'])
        if params["side"] == "SELL":
            stopPrice = self.getLimitPrice(params['takeProfit'])

        price = self.getLastPrice()
        quantity = params["quantity"]

        return {"stopPrice": stopPrice, "price": price, "quantity": quantity}

    def TakeProfitMarket(self, params):
        """Process the values of take profit Limit order"""
        stopPrice = 0
        if params["side"] == 'BUY':
            stopPrice = self.getLimitPrice(params['takeProfit'])
        if params["side"] == "SELL":
            stopPrice = self.getTakeProfit(params['takeProfit'])
        
        quantity = params["quantity"]

        return {"timeInForce": self.timeInForce, "stopPrice": stopPrice, "quantity": quantity}
    
    def stopMarket(self, params):
        """Process the values of take profit Limit order"""
        stopPrice = 0
        if params["side"] == 'BUY':
            stopPrice = self.getTakeProfit(params['takeProfit'])
        if params["side"] == "SELL":
            stopPrice = self.getLimitPrice(params['takeProfit'])
        
        price = self.getLastPrice()
        quantity = params["quantity"]

        return {"timeInForce": self.timeInForce, "stopPrice": stopPrice, "quantity": quantity}
        
    def trailingStopMarket(self, params):
        """Process the values of take profit Limit order"""
        quantity = params["quantity"]
        callbackRate = params["callbackRate"]

        return {"timeInForce": self.timeInForce, "quantity": quantity, "callbackRate":callbackRate}

    def sendOrder(self, params):
        # params in is json/dictionary
        # params = {'symbol':trade_symbol, 'side':'None', 'type':'None', timeInForce':'None','quantity':'None','quoteOrderQty':'None','price':'None', 'callbackRate':None }
        # This function takes all order types
        if self.is_authentic == True:
            orderDetails = self.orderToPlaceProcessor(params)
            print("ORDER DETAILS PARAMS",orderDetails)
            res = self.futures_create_order(**orderDetails)
            return res
        else:
            return self.is_authentic

    # FIXME This method needs a serious rethink. and redesign

    def orderToPlaceProcessor(self, params):
        # TODO check previous positions
        order_basics = {"symbol": params["symbol"], "type": params['type'],
                        "side": params["side"], "quantity": params["quantity"]}
        if 'reduceOnly' in params:
            order_basics.update({'reduceOnly':'true'})
        open_orders = self.checkAllOPenOrders()
        print('Open Order', open_orders)
        if open_orders == False:
            if params["type"] == 'MARKET':
                pass
            elif params["type"] == 'LIMIT':
                print("inside LIMIT")
                order_basics.update(self.LimitOrder(params))
                print("order_basics", order_basics)
            elif params["type"] == 'TAKE_PROFIT':
                order_basics.update(self.takeProfitOrder(params))
            
            elif params["type"] == 'STOP' :
                order_basics.update(self.StopOrder(params))

            elif params["type"] == 'STOP_MARKET':
                order_basics.update(self.stopMarket(params))

            elif params["type"] == 'TAKE_PROFIT_MARKET' :
                order_basics.update(self.TakeProfitMarket(params))

            elif params["type"] == 'TRAILING_STOP_MARKET':
                order_basics.update(self.trailingStopMarket(params))

            print("paramsssssssssss", order_basics)
            return order_basics
        else:
            print("This code executed")
            # extract side
            # extract quantity
            # leverage
            positionQty = open_orders[0]['origQty']
            positionSide = open_orders[0]['side']
            positionOrderId = open_orders[0]['orderId']

            paramsCancel = {
                "orderId": positionOrderId,
                "symbol":self.trade_symbol
            }

            # cancel_ret = self.futures_cancel_all_open_orders(**paramsCancel)
            # print('cancel order------------ ', cancel_ret)

            if params["type"] == 'MARKET':
                pass
            elif params["type"] == 'LIMIT':
                order_basics.update(self.LimitOrder(params))

            elif params["type"] == 'TAKE_PROFIT':
                order_basics.update(self.takeProfitOrder(params))
            
            elif params["type"] == 'STOP' :
                order_basics.update(self.StopOrder(params))

            elif params["type"] == 'STOP_MARKET':
                order_basics.update(self.stopMarket(params))

            elif params["type"] == 'TAKE_PROFIT_MARKET' :
                order_basics.update(self.TakeProfitMarket(params))

            elif params["type"] == 'TRAILING_STOP_MARKET':
                order_basics.update(self.trailingStopMarket(params))

            print("paramsssssssssss", order_basics)
            return order_basics

            

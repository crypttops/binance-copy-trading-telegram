import requests

def convert_usdt_to_base_asset(symbol, amount_in_usdt, leverage):
    order_amount = float(amount_in_usdt)*float(leverage)
    data = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
    return float(order_amount)/float(data.json()['price'])

# data = convert_usdt_to_base_asset("BTCUSDT", 20)
# print(data)

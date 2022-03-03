import requests

def convert_usdt_to_base_asset(symbol, amount_in_usdt, leverage):
    order_amount = float(amount_in_usdt)*float(leverage)
    data = requests.get(f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}')
    return float(order_amount)/float(data.json()['lastPrice'])

def get_last_price_ticker(symbol):
    data = requests.get(f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}')
    return data.json()['lastPrice']


# data = convert_usdt_to_base_asset("BTCUSDT", 20)
# print(data)
# resp1 = get_last_price_ticker("RENUSDT")
# resp2 = convert_usdt_to_base_asset("RENUSDT",10, 20)

# print(resp1)
# print(resp2)
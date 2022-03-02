rawsignal = """
foobar/USDT SHORT 🛑
Leverage 20x
Entries 0.226
Target 1 0.222
Target 2 0.216
Target 3 0.209
Target 4 0.198
Target 5 0.180

SL 0.242
"""

import json
import re

def extractSymbol(rsignal):
    """
    This function takes the raw signal and returns symbol
    """
    for i in rsignal:
        # parser = re.search(r"BLZ\w+|GBP\w+|EUR\w+|NZD\w+|CAD\w+|JPY\w+|AUD\w+", i,  flags=re.IGNORECASE)
        # parser = re.search(r"^.*[,-/].*$", i,  flags=re.IGNORECASE) working
        parser = re.search(r"^.*[,-/]USDT|^.*[,-/]BTC", i,  flags=re.IGNORECASE)

        if bool(parser)==True:
            parser_span = parser.span()
            symbol = parser.string[parser_span[0]:parser_span[1]]
            return symbol
            

def extractSide(rsignal):
    """
    This function takes the input signal and  returns the side
    """
    for i in rsignal: 
        parser = re.search(r"BUY|SELL|Sell|sell|SHORT|LONG", i,  flags=re.IGNORECASE)
        if bool(parser) == True:
            parser_span = parser.span()
            side = parser.string[parser_span[0]:parser_span[1]]
            return side
            break

def extractTps(rsignal):
    """
    This function takes the raw signal and returns a list of takeprofits extracted from the signal
    """
    take_profit = []
    for i in rsignal: 
        parser = re.search(r"[Target|TP|TP\d+](\s|[at@\s]|[\d]|[,-]|[0-9])(\d+\.\d+)", i,  flags=re.IGNORECASE)
        if bool(parser) == True:
            parser_span = parser.span()
            tpstring = parser.string[parser_span[0]:parser_span[1]]
            tp_parse = re.findall(r'\d+\.\d+', tpstring, flags=re.IGNORECASE)
            for tp in tp_parse:
                take_profit.append(float(tp))
    return take_profit            

       
def extractSls(rsignal):
    """
    This function takes the raw signal and returns a list of takeprofits extracted from the signal
    """
    stop_loss = []
    for i in rsignal: 
        parser = re.search(r"(STOPLOSS|SL|SL\d+)(\s|[at@\s]|[\d]|[,-]|[0-9])(\d+\.\d+)", i,  flags=re.IGNORECASE)
        if bool(parser) == True:
            parser_span = parser.span()
            slstring = parser.string[parser_span[0]:parser_span[1]]
            sl_parse = re.findall(r'\d+\.\d+', slstring, flags=re.IGNORECASE)
            for sl in sl_parse:
                stop_loss.append(float(sl))

    return float(sl)    


        
def extractEP(rsignal):
    entry_price = []
    for i in rsignal:
        parser = re.search(r"[ENTRY|Entries](\s|[at@\s]|[\d]|[,-]|[0-9])([a-z]+)(\s)(\d+\.\d+)", i, flags=re.IGNORECASE)
        # Parser2 = re.search(r"(BUY|SELL)([at@\s][\d+\.\d+])", i,  flags=re.IGNORECASE)
        if bool(parser) == True:
            parser_span = parser.span()
            epstring = parser.string[parser_span[0]:parser_span[1]]
            ep_parse = re.findall(r'\d+\.\d+', epstring, flags=re.IGNORECASE)
            for ep in ep_parse:
                entry_price.append(float(ep))
    return float(ep)


def cleanOrderData(rawsignal):
    """
    Cleans the signal and returns a dictionary
    """
    order_data = {}
    rsignal = rawsignal.split("\n")
    response = {}
    symbol = extractSymbol(rsignal)
    side = extractSide(rsignal)
    tps = extractTps(rsignal)
    sl = extractSls(rsignal)
    ep = extractEP(rsignal)


    response.update({"symbol":symbol, "side":side, 'ep':ep, 'tps':tps, 'sl':sl})
    return response
   

def processDataFor3commas(raw_signal):
    signal_data = cleanOrderData(raw_signal)
    """
    This builds a template order that will be used by various users to create orders in 3commas
    MISSING account_id 
    MISSING POSITION-UNITS-VALUE to be passed while pushing the order

    MISSING TO BE INJECTED LATER
    """
    order_data ={"account_id":None}
    order_bid_or_ask =''
    if not signal_data['symbol']:
        return False
    order_data.update({"pair":"USDT_"+signal_data['symbol'].strip().replace('/', '').upper()})
    if not signal_data['side']:
        return False

    if signal_data['side'].lower() in ["buy","long"]:
        order_bid_or_ask = 'bid'
        order_side = "buy"
    elif signal_data['side'].lower() in ["short", "sell"]:
        order_bid_or_ask = "ask"
        order_side="sell"

    order_data.update({"position":
                        {
                            "type":order_side,
                            "units":{
                                "value": None
                            },
                            "price":{
                             "value":float(signal_data['ep'])
                            },
                            "order_type":"limit"
                            
                        }})
    if not signal_data["tps"]:
        return False

    tp_length = len(signal_data['tps'])
    steps =[]
    for tp in signal_data['tps']:
        tp_data={
        "order_type": "limit",
        "price": {
          "value": float(tp),
          "type": order_bid_or_ask,
        },
        "volume": (100/tp_length)
        }
        steps.append(tp_data)
    order_data.update({"take_profit":
    {
        "enabled":True,
        "steps":steps
    }})
    
    if not signal_data['sl']:
        return False
    order_data.update({"stop_loss":{
    "enabled":True,
    "order_type": "limit",
    "price": {
      "value": float(signal_data['sl'])
    
    },
    "conditional": {
      "price": {
        "value": float(signal_data['sl']),
        "type": order_bid_or_ask
      }
    },
    "timeout": {
      "enabled": False,
      "value": 8
    }
    }})
    return order_data

# result = cleanOrderData(rawsignal)
# print(result)
# data3c = processDataFor3commas(result)
# print(json.dumps(data3c, indent=4))
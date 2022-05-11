from operator import le


def pnlCalc(config):
    position_size = float(config['position_size'])
    order_side = config['order_side']
    entry_price = float(config['entry_price'])
    last_price = float(config['last_price'])
    contract_multiplier = float(config['contract_multiplier'])
    leverage = float(config['leverage'])

    IMR = 1/leverage

    order_direction = 1 if order_side.lower()=='buy' else -1
    unrealized_PNL = position_size * order_direction * (last_price - entry_price)  
    entry_margin = position_size * contract_multiplier * last_price* IMR
    perc_roe = (unrealized_PNL/ entry_margin)*100
    return unrealized_PNL, perc_roe

def getTpEntryPrice(order_side, entry_price, perc_profit, leverage):
    IMR = 1/float(leverage)
    contract_multiplier=1
    order_direction = 1 if order_side.lower()=='buy' else -1
    N = float(entry_price)
    D = (float(perc_profit)*float(contract_multiplier)*IMR)/(order_direction*100) -1
    tp_price =(N/D)/(-1)
    return tp_price
    
    

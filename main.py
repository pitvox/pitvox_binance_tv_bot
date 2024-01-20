import time
from flask import Flask, request
from binance.client import Client # pip install python-binance
from config import *
import datetime
import math
import requests
from log_module import CustomLogger

client = Client(API_KEY, API_SECRET)
app = Flask(__name__)

current_status = CURRENT_STS
current_order_amount = None

logger = CustomLogger(LOG_FILE)

try:
    logger.log("info", "Changing position mode to One-way ...")
    result = client.futures_change_position_mode(dualSidePosition=False)
    logger.log("info", result)
except Exception as e:
    logger.log("info", "Already in One-way mode")

# client.futures_change_margin_type(symbol=symbol, marginType="ISOLATED")
# logger.log("info", "Margin type is changed to ISOLATED")


def get_current_margin_balance():
    for asset in client.futures_account()["assets"]:
        if (asset["asset"] == "USDT"):
            usdt_balance_now = float(asset["marginBalance"])
    logger.log("info", "Current USDT margin balance: "+str(usdt_balance_now))
    return usdt_balance_now

get_current_margin_balance()

def f_sellable_quantity(symbol, quantity):
    info = client.futures_exchange_info()
    for sym in info["symbols"]:
        if (sym["symbol"] == symbol):
            quantity_precision = int(sym["quantityPrecision"])
            print("quantity_precision: " + str(quantity_precision))
            break
    quantity = math.floor((quantity) * 10 ** quantity_precision) / 10 ** quantity_precision
    return quantity
def execute_order(side, action, future_status):
    global current_status
    global current_order_amount
    try:
        changed_leverage = client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)["leverage"]
        logger.log("info", "Changed leverage to: " + str(changed_leverage))

        current_usdt_amount = get_current_margin_balance()
        if(action == "open"):
            raw_coin_amount = ((current_usdt_amount * ORDER_VAL_PERCENTAGE / 100) * LEVERAGE) / float(client.get_ticker(symbol=SYMBOL)["lastPrice"])
            coin_amount = f_sellable_quantity(SYMBOL, raw_coin_amount)
        if(action == "close"):
            coin_amount = current_order_amount
        logger.log("info", "coin_amount: " + str(coin_amount))
        logger.log("info", "side: " + str(side))

        order = client.futures_create_order(symbol=SYMBOL, side=side, type="MARKET", quantity=coin_amount)
        order_id = order["orderId"]
        time.sleep(1)
        order_details = client.futures_get_order(symbol=SYMBOL, orderId=order_id)
        logger.log("info", str(order_details))
        current_status = future_status
        current_order_amount = coin_amount
        get_current_margin_balance()
    except Exception as e:
        logger.log("error", "Error in execute_order -> " + str(e))

def get_order_details(alert):
    if "long" in alert and "open" in alert:
        return "BUY", "open", "long opened"
    elif "long" in alert and "close" in alert:
        return "SELL", "close", "no open positions"
    elif "short" in alert and "open" in alert:
        return "SELL", "open", "short opened"
    elif "short" in alert and "close" in alert:
        return "BUY", "close", "no open positions"
    else:
        return None, None

@app.route("/tv_webbhook", methods=['POST'])
def tv_webbhook():
    alert = request.get_data(as_text=True)
    alert = alert.lower()
    logger.log('info', "#################### ALERT from tradingview: " + alert)
    side, action, future_status = get_order_details(alert)
    if(side != None):
        if("long" in alert and not IS_ENABLE_LONG):
            logger.log('info', "long positions are disabled")
            return "long positions are disabled"
        if ("short" in alert and not IS_ENABLE_SHORT):
            logger.log('info', "short positions are disabled")
            return "short positions are disabled"
        logger.log('info', "current_status: " + current_status)
        if(current_status == "no open positions"):
            if(action == "open"):
                execute_order(side, action, future_status)
            else:
                logger.log('info', "There is no open positions to close. Skipping this alert.")
        elif(current_status == "long opened"):
            if(action == "close" and side == "SELL"):
                execute_order(side, action, future_status)
            else:
                logger.log('info', "Expecting closing long positions alerts only. Skipping this alert.")
        elif (current_status == "short opened"):
            if (action == "close" and side == "BUY"):
                execute_order(side, action, future_status)
            else:
                logger.log('info', "Expecting closing short positions alerts only. Skipping this alert.")
        return "done"
    else:
        return "not a valid alert"



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80, threaded=False)
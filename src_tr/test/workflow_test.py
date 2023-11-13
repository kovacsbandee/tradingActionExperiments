import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from checks.checks import check_trading_day
from utils.utils import calculate_scanning_day, get_nasdaq_stickers
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Position
import pandas as pd
import logging
logging.basicConfig(level=logging.DEBUG)

from src_tr.main.scanners.AndrewAzizRecommendedScanner import AndrewAzizRecommendedScanner
from src_tr.main.data_generators.AlpacaPriceDataGenerator import AlpacaPriceDataGenerator
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.helpers.converter import string_to_dict_list
from src_tr.main.helpers.get_latest_bar_data import get_alpaca_bar_data
from src_tr.main.enums_and_constants.trading_constants import *

load_dotenv()
PROJECT_PATH = os.environ["PROJECT_PATH"]
STICKER_CSV_PATH = os.environ["STICKER_CSV_PATH"]
ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)

# 1) Scanner inicializálása -> watchlist létrehozás
trading_day = check_trading_day('2023-10-16')
scanning_day = calculate_scanning_day(trading_day)
stickers = get_nasdaq_stickers(project_path=PROJECT_PATH, file_path=STICKER_CSV_PATH)
scanner = AndrewAzizRecommendedScanner(name="AzizScanner",
                                       trading_day=trading_day,
                                       scanning_day=scanning_day,
                                       stickers=stickers,
                                       lower_price_boundary=10,
                                       upper_price_boundary=400,
                                       price_range_perc_cond=10,
                                       avg_volume_cond=25000,
                                       #std_close_lower_boundary_cond=0.25
                                       )
#scanner.calculate_filtering_stats(save_csv=False)
#rec_st_list = scanner.recommend_premarket_watchlist()
TEST_SYMBOL = "METC"
rec_st_list = [TEST_SYMBOL]
#print([s for s in rec_st_list])

# 2) PriceDataGenerator inicializálás
data_generator = AlpacaPriceDataGenerator(#trading_day=trading_day,
                                          recommended_sticker_list=rec_st_list
                                          )
strategy = None

def on_open(ws):
    global strategy
    print("opened")
    data_generator.initialize_sticker_dict()
    data_generator.initialize_sticker_df()
    auth_data = {"action": "auth", "key": f"{ALPACA_KEY}", "secret": f"{ALPACA_SECRET_KEY}"}

    ws.send(json.dumps(auth_data))

    listen_message = {
        "action":"subscribe",
        "bars":[TEST_SYMBOL]
        }

    ws.send(json.dumps(listen_message))
    
    # initialize strategy
    initial_capital = float(trading_client.get_account().cash)
    strategy = StrategyWithStopLoss(ma_short=5,
                                ma_long=12,
                                stop_loss_perc=0.0,
                                epsilon=0.01,
                                initial_capital=initial_capital
                                )
    #data_generator.sticker_df[TEST_SYMBOL] = get_latest_bar_data(alpaca_key=ALPACA_KEY, 
    #                                                        alpaca_secret_key=ALPACA_SECRET_KEY,
    #                                                        input_symbol=TEST_SYMBOL)
    #strategy.set_sticker_df(data_generator.sticker_df[TEST_SYMBOL])
    strategy.initialize_additional_fields()
    print("Capital at the opening of trading session: " + str(strategy.capital))
    
def on_message(ws, message):
    global strategy, trading_client
    try:
        print("New bar data received at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        minute_bars = string_to_dict_list(message)

        if minute_bars[0]['T'] == 'b':
            data_generator.update_sticker_df(minute_bars=minute_bars)       
            #ITT JÖN A MEDZSIK
            #TODO: data_generator.sticker_df most akkor egy DataFrame, vagy dict? úgy tűnik, hogy dict
            sticker_df_length = len(data_generator.sticker_df[TEST_SYMBOL])
            str_ma_long_value = int(strategy.ma_long)
            if sticker_df_length > str_ma_long_value:
                strategy.set_sticker_df(data_generator.sticker_df[TEST_SYMBOL]) #TODO: itt lehet galiba, ha nem dataframe
                strategy.update_capital_amount(float(trading_client.get_account().cash))
                strategy.apply_strategy(trading_client=trading_client,
                                        symbol=TEST_SYMBOL)
                
                sticker_df = strategy.sticker_df #TODO: itt lehet galiba, ha nem dataframe

                trading_action = sticker_df.iloc[-1][TRADING_ACTION]
                current_position = sticker_df.iloc[-2][POSITION] #NOTE: próba cseresznye
                quantity = sticker_df.iloc[-1][CURRENT_CAPITAL] / sticker_df.iloc[-1][CLOSE]

                # kurvanagy TODO: 
                if trading_action == ACT_BUY_NEXT_LONG and current_position == POS_OUT:
                    place_buy_order(quantity)
                    # refresh position in sticker_df?
                #elif trading_action == ACT_SELL_NEXT_SHORT and current_position == POS_OUT:
                #    place_sell_order(quantity)
                #    # refresh position in sticker_df?
                elif trading_action == ACT_SELL_PREV_LONG and current_position == POS_LONG_BUY:
                    close_current_position("Sell previous long")
                #elif trading_action == ACT_BUY_PREV_SHORT and current_position == POS_SHORT_SELL:
                #    close_current_position("Buy previous long")
                else:
                    print(ACT_NO_ACTION)
            else:
                print("Not enough data to apply strategy")
        else:
            print('Authentication and data initialization')
    except Exception as e:
        print(str(e))
        
def place_buy_order(quantity):
    global trading_client
    try:
        market_order_data = MarketOrderRequest(
                        symbol=TEST_SYMBOL,
                        qty=quantity,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )
        trading_client.submit_order(
                        order_data=market_order_data
                    )
        print('Buy order completed')
    except Exception as e:
        print(str(e))

def place_sell_order(quantity):
    global trading_client
    try:
        market_order_data = MarketOrderRequest(
                        symbol=TEST_SYMBOL,
                        qty=round(quantity),
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                        )
        trading_client.submit_order(
                        order_data=market_order_data
                    )
        print('Sell order completed')
    except Exception as e:
        print(str(e))

def close_current_position(position):
    global trading_client
    try:
        trading_client.close_position(TEST_SYMBOL)
        print(f'{position} position closed successfully')
    except Exception as e:
        print(str(e))
    
def on_ping(ws, ping_payload):
    print(f"Ping sent: {ping_payload}")
    
def on_pong(ws, pong_payload):
    print(f"Pong received: {pong_payload}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed with status code {close_status_code}: {close_msg}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

    
socket = SOCKET_URL

ws = websocket.WebSocketApp(url=socket, 
                            on_open=on_open,
                            on_message=on_message,
                            on_close=on_close,
                            on_error=on_error,
                            on_ping=on_ping,
                            on_pong=on_pong
                            )
ws.run_forever(reconnect=True, ping_interval=30, ping_timeout=10)
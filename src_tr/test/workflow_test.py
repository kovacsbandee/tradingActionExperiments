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

from src_tr.main.scanners.AndrewAzizRecommendedScanner import AndrewAzizRecommendedScanner
from src_tr.main.data_generators.AlpacaPriceDataGenerator import AlpacaPriceDataGenerator
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.helpers.converter import string_to_dict_list

load_dotenv()
PROJECT_PATH = os.environ["PROJECT_PATH"]
STICKER_CSV_PATH = os.environ["STICKER_CSV_PATH"]
ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]
# paper=True enables paper trading
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
                                       std_close_lower_boundary_cond=0.25)
#scanner.calculate_filtering_stats(save_csv=False)
#rec_st_list = scanner.recommend_premarket_watchlist()
rec_st_list = ["RARE"]
#print([s for s in rec_st_list])

# 2) PriceDataGenerator inicializálás
data_generator = AlpacaPriceDataGenerator(trading_day=trading_day,
                                          recommended_sticker_list=rec_st_list,
                                          lower_price_boundary=10,
                                          upper_price_boundary=100,
                                          lower_volume_boundary=0,
                                          data_window_size=10)
prev_close_price = None
curr_close_price = None
curr_position = 'out'
capital = float(trading_client.get_account().cash)
strategy = None


def on_open(ws):
    global strategy
    print("opened")
    data_generator.initialize_sticker_dict()
    data_generator.initialize_current_data_window()
    auth_data = {"action": "auth", "key": f"{ALPACA_KEY}", "secret": f"{ALPACA_SECRET_KEY}"}

    ws.send(json.dumps(auth_data))

    listen_message = {
        "action":"subscribe",
        "bars":["AAPL"]
        }

    ws.send(json.dumps(listen_message))
    strategy = StrategyWithStopLoss(ma_short=5,
                                ma_long=12,
                                stop_loss_perc=0.0,
                                epsilon=0.01,
                                initial_capital=capital
                                )
    print("Capital at the opening of trading session: " + capital)
    
def on_message(ws, message):
    global data_generator, prev_close_price, curr_close_price, curr_position
    print("New bar data received")
    minute_bars = string_to_dict_list(message)

    if minute_bars[0]['T'] == 'b':
        data_generator.update_current_data_window(minute_bars=minute_bars)
        print(data_generator.sticker_df['AAPL'])
        
        curr_close_price = _get_current_close_price()

        if len(data_generator.sticker_df['AAPL']) >= strategy.ma_long:
            

            
        if len(data_generator.sticker_df['AAPL']) >= 2: #ma_long
            case_init = prev_close_price is None and curr_position == 'out'
            case_long_sell = not case_init and curr_close_price < prev_close_price and curr_position == 'long'
            case_long_buy = not case_init and curr_close_price > prev_close_price and curr_position == 'out'
            case_short_buy = not case_init and curr_close_price > prev_close_price and curr_position == 'short'
            
            if case_init:
                prev_close_price = _get_prev_close_price()
                if curr_close_price > prev_close_price:
                    curr_position = 'long'
                    # buy
                    print("Buying")
                    place_buy_order()
            elif case_long_sell:
                prev_close_price = curr_close_price
                curr_position = 'short'
                # sell
                print("Selling")
                place_sell_order()
            elif case_short_buy or case_long_buy:
                prev_close_price = curr_close_price
                curr_position = 'long'
                # buy
                print("Buying")
                place_buy_order()
            else:
                print("No action")
        
        prev_close_price = _get_prev_close_price()
        curr_close_price = _get_current_close_price()
        
        print(f"Current close price: {curr_close_price}")
        print(f"Previous close price: {prev_close_price}")
        print(f"Current position: {curr_position}")
    else:
        print('Authentication and data initialization')
        
def _get_current_close_price():
    global data_generator
    curr_close_index = datetime.strptime(data_generator.sticker_df['AAPL'].index[-1], '%Y-%m-%dT%H:%M:%SZ')
    curr_close_time = curr_close_index.strftime('%Y-%m-%dT%H:%M:%SZ')
    curr_close_price = data_generator.sticker_df['AAPL'].loc[curr_close_time, 'c']
    return curr_close_price

def _get_prev_close_price():
    global data_generator
    prev_close_index = datetime.strptime(data_generator.sticker_df['AAPL'].index[-2], '%Y-%m-%dT%H:%M:%SZ')
    prev_close_time = prev_close_index.strftime('%Y-%m-%dT%H:%M:%SZ')
    prev_close_price = data_generator.sticker_df['AAPL'].loc[prev_close_time, 'c']
    return prev_close_price

def place_buy_order():
    global trading_client, capital, curr_close_price
    quantity = capital / curr_close_price
    try:
        market_order_data = MarketOrderRequest(
                        symbol="AAPL",
                        qty=quantity,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )
        trading_client.submit_order(
                        order_data=market_order_data
                    )
    except:
        print("Error in placing buy order")

def place_sell_order():
    global trading_client, capital, curr_close_price
    quantity = capital / curr_close_price
    try:
        market_order_data = MarketOrderRequest(
                        symbol="AAPL",
                        qty=quantity,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                        )
        trading_client.submit_order(
                        order_data=market_order_data
                    )
    except:
        print("Error in placing sell order")
    
    #market_order_data = MarketOrderRequest(
    #                symbol="AAPL",
    #                qty=0.8,
    #                side=OrderSide.BUY,
    #                time_in_force=TimeInForce.DAY
    #                )
    #
    #market_order = trading_client.submit_order(
    #                order_data=market_order_data
    #            )

    #account = trading_client.get_account()
    #position = [p for p in trading_client.get_all_positions() if p.symbol == "AAPL"]
    #current_position = position[0].side if position else "out"
    #
    #print("Symbol: " + position[0].symbol)
    #print("Current position: " + current_position)
    #print("Capital: " + account.cash)
    #print("Order data: " + market_order)
    
socket = SOCKET_URL

ws = websocket.WebSocketApp(socket, 
                            on_open=on_open,
                            on_message=on_message)

ws.run_forever()

# 3) Stratégia, DataStream, TradingClient inicializálás
#NOTE: stop_loss_strategy_test.py

# 4) WebSocket inicializálás (ping interval fontos!)

# 5) TradingManager inicializálás, priceData ősfeltöltés
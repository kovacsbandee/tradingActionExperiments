import os
import time as epoch_time
from datetime import datetime, time as dt_time
from dotenv import load_dotenv
from src_tr.main.checks.checks import check_trading_day
from utils.utils import calculate_scanning_day, get_nasdaq_stickers
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Position
import pandas as pd
#import logging
#logging.basicConfig(level=logging.DEBUG)

from src_tr.main.helpers.get_latest_bar_data import get_yahoo_data
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.enums_and_constants.trading_constants import *

load_dotenv()
ALPACA_KEY= os.environ["ALPACA_KEY"]
ALPACA_SECRET_KEY= os.environ["ALPACA_SECRET_KEY"]
SOCKET_URL= os.environ["SOCKET_URL"]

trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET_KEY, paper=True)

TEST_SYMBOL = "AAPL"
rec_st_list = [TEST_SYMBOL]

data_generator = PriceDataGeneratorMain(recommended_sticker_list=rec_st_list)
yahoo_data = get_yahoo_data(sticker=TEST_SYMBOL, 
                            start_date=datetime(2023, 11, 13), 
                            end_date=datetime(2023, 11, 14),
                            n_last_bars=1)
data_generator.sticker_df[TEST_SYMBOL] = yahoo_data

#data_generator.initialize_sticker_dict()
#data_generator.initialize_sticker_df()
initial_capital = float(trading_client.get_account().cash)

strategy = StrategyWithStopLoss(ma_short=5,
                            ma_long=12,
                            stop_loss_perc=0.0,
                            epsilon=0.01,
                            initial_capital=initial_capital
                            )
strategy.set_sticker_df(data_generator.sticker_df[TEST_SYMBOL])
strategy.initialize_additional_fields()

def run_trading():
    market_close_datetime = datetime.combine(datetime.today(), dt_time(20, 0, 0))
    current_time = datetime.now().time()

    is_open = datetime.combine(datetime.today(), current_time) > datetime.combine(datetime.today(), dt_time(9, 30, 0)) and datetime.combine(datetime.today(), current_time) < market_close_datetime

    print(is_open)
    while is_open:
        #start_time = time.time() #epoch seconds e.g.: 1699788456.5225582
        now = epoch_time.localtime() 
        print(f"{now.tm_hour}:{now.tm_min}:{now.tm_sec}")
        try:
            yahoo_start = datetime.today()
            yahoo_end = datetime.today()
            minute_bars = get_yahoo_data(sticker=TEST_SYMBOL, start_date=yahoo_start, end_date=yahoo_end, n_last_bars=1)
            
            print(minute_bars)
            data_generator.update_sticker_df_yahoo(minute_bars=minute_bars)
            sticker_df_length = len(data_generator.sticker_df[TEST_SYMBOL])
            str_ma_long_value = int(strategy.ma_long)
            if sticker_df_length > str_ma_long_value:
                strategy.set_sticker_df(data_generator.sticker_df[TEST_SYMBOL])
                strategy.update_capital_amount(float(trading_client.get_account().cash))
                strategy.apply_long_strategy(trading_client=trading_client,
                                        symbol=TEST_SYMBOL)
                
                sticker_df = strategy.sticker_df

                trading_action = sticker_df.iloc[-1][TRADING_ACTION]
                current_position = sticker_df.iloc[-2][POSITION]
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
                print(data_generator.sticker_df[TEST_SYMBOL])
            else:
                print("Not enough data to apply strategy")
        except Exception as e:
            print(str(e))

        # WAIT FOR NEXT DATA
        epoch_time.sleep(10)
        
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
        
run_trading()
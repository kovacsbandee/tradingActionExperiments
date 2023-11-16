from datetime import datetime
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import pandas as pd
import threading

from src_tr.main.scanners.ScannerBase import ScannerBase
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.helpers.converter import string_to_dict_list
from src_tr.main.enums_and_constants.trading_constants import *

class TradingManagerMain():

    def __init__(self,
                data_generator: PriceDataGeneratorMain,
                strategy: StrategyWithStopLoss,
                trading_client: TradingClient,
                api_key: str,
                secret_key: str,
                #market_open: datetime,
                #market_close: datetime
                ):
        #self.scanner = scanner
        self.data_generator = data_generator
        self.strategy = strategy
        self.trading_client = trading_client
        self.api_key = api_key
        self.secret_key = secret_key
        self.event = threading.Event()
        self.minute_bars = []
        #self.market_open = market_open
        #self.market_close = market_close

    def handle_message(self, ws, message):
        try:
            print("New bar data received at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            minute_bars = string_to_dict_list(message)
            if minute_bars[0]['T'] == 'b':
                for item in minute_bars:
                    self.minute_bars.append(item)
                    if len(self.minute_bars) == len(self.data_generator.recommended_sticker_list):
                        self.execute_all()
                        self.minute_bars = []
                        print('Data available, execute() called')

            else:
                print('Authentication and data initialization')
        except Exception as e:
            print(str(e))
        

    def on_open(self, ws: websocket.WebSocketApp):
        print(f"WebSocket connection opened on URL: {ws.url}")
        self.data_generator.initialize_sticker_dict()
        auth_data = {"action": "auth", "key": f"{self.api_key}", "secret": f"{self.secret_key}"}

        ws.send(json.dumps(auth_data))

        #NOTE: polygon -> {"action":"subscribe", "params":"AM.AAPL,AM.TSLA,AM.MSFT"}
        listen_message = {
            "action":"subscribe",
            "bars": self.data_generator.recommended_sticker_list
            }

        ws.send(json.dumps(listen_message))
        
    def execute_all(self):
        try:
            self.data_generator.update_sticker_df(minute_bars=self.minute_bars)
            
            # apply strategy on all stickers TODO: kiszervezni külön metódusba
            for symbol, value_dict in self.data_generator.sticker_dict.items():
                sticker_df_length = len(value_dict[STICKER_DF]) 
                str_ma_long_value = int(self.strategy.ma_long) #NOTE: redundáns int parse?
                if sticker_df_length > str_ma_long_value:
                    self.data_generator.sticker_dict[symbol] = self.strategy.apply_long_strategy(trading_client=self.trading_client, 
                                                                            symbol=symbol,  
                                                                            sticker_dict=value_dict)
                else:
                    print("Not enough data to apply strategy")

            # execute trading actions TODO: kiszervezni külön metódusba
            for symbol, value_dict in self.data_generator.sticker_dict.items():
                sticker_df_length = len(value_dict[STICKER_DF]) 
                str_ma_long_value = int(self.strategy.ma_long) #NOTE: redundáns int parse?
                if sticker_df_length > str_ma_long_value:
                    current_df: pd.DataFrame = value_dict[STICKER_DF]
                    trading_action = current_df.iloc[-1][TRADING_ACTION]
                    current_position = current_df.iloc[-2][POSITION]

                    # divide capital with amount of OUT positions:
                    out_positions = self.data_generator.get_out_positions()
                    quantity_buy_long = current_df.iloc[-1][CURRENT_CAPITAL] / out_positions / current_df.iloc[-1][CLOSE]
                    #NOTE sell only a percentage of divided capital
                    quantity_sell_short = (current_df.iloc[-1][CURRENT_CAPITAL] / out_positions * 0.15) / current_df.iloc[-1][CLOSE]

                    # TODO: 
                    if trading_action == ACT_BUY_NEXT_LONG and current_position == POS_OUT:
                        self.place_buy_order(quantity_buy_long, symbol)
                        # refresh position in sticker_df?
                    elif trading_action == ACT_SELL_NEXT_SHORT and current_position == POS_OUT:
                        self.place_sell_order(quantity_sell_short, symbol)
                        # refresh position in sticker_df?
                    elif trading_action == ACT_SELL_PREV_LONG and current_position == POS_LONG_BUY:
                        self.close_current_position("Sell previous long", symbol)
                    elif trading_action == ACT_BUY_PREV_SHORT and current_position == POS_SHORT_SELL:
                        self.close_current_position("Buy previous long", symbol)
                    else:
                        print(ACT_NO_ACTION)                    
        except Exception as e:
            print(str(e))
            
    def place_buy_order(self, quantity, symbol):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=quantity,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(
                            order_data=market_order_data
                        )
            print('Buy order completed')
        except Exception as e:
            print(str(e))

    def place_sell_order(self, quantity, symbol):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=round(quantity), #TODO: kell kerekítés?
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(
                            order_data=market_order_data
                        )
            print('Sell order completed')
        except Exception as e:
            print(str(e))

    def close_current_position(self, position, symbol):
        try:
            self.trading_client.close_position(symbol)
            print(f'{position} position closed successfully')
        except Exception as e:
            print(str(e))
        
    def on_ping(self, ws, ping_payload):
        print(f"Ping sent: {ping_payload}")
        
    def on_pong(self, ws, pong_payload):
        print(f"Pong received: {pong_payload}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed with status code {close_status_code}: {close_msg}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
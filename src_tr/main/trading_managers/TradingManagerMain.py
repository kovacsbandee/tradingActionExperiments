from datetime import datetime
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import pandas as pd

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
                minutes_before_trading_start: int,
                rsi_threshold: int
                #market_open: datetime,
                #market_close: datetime
                ):
        self.data_generator = data_generator
        self.strategy = strategy
        self.trading_client = trading_client
        self.api_key = api_key
        self.secret_key = secret_key
        self.minute_bars = []
        self.stickers_to_delete = []
        self.rsi_filtered = False
        self.minutes_before_trading_start = minutes_before_trading_start
        self.rsi_threshold = rsi_threshold
        #self.market_open = market_open
        #self.market_close = market_close

    def handle_message(self, ws, message):
        try:
            print(f"New bar data received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
            "bars": [s[SYMBOL] for s in self.data_generator.recommended_sticker_list]
            }

        ws.send(json.dumps(listen_message))
        
    def execute_all(self):
        try:
            self.data_generator.update_sticker_df(minute_bars=self.minute_bars)
            
            # apply strategy on all stickers --- TODO: kiszervezni külön metódusba
            for symbol, value_dict in self.data_generator.sticker_dict.items():
                sticker_df_length = len(value_dict[STICKER_DF])
                ma_long_value = self.strategy.ma_long
                if sticker_df_length >= ma_long_value:
                    current_capital = self.get_current_capital()
                    self.strategy.update_capital_amount(current_capital)
                    previous_position = self.get_previous_position(symbol)
                    self.data_generator.sticker_dict[symbol] = self.strategy.apply_long_strategy(previous_position=previous_position, 
                                                                                                 symbol=symbol,  
                                                                                                 sticker_dict=value_dict)
                    current_df: pd.DataFrame = value_dict[STICKER_DF]
                    if len(current_df) >= self.minutes_before_trading_start:
                        if not self.rsi_filtered and current_df[RSI].mean() > self.rsi_threshold:
                            self.stickers_to_delete.append(symbol)
                        if self.rsi_filtered:
                            self.execute_trading_action(symbol, current_df)
                    else:
                        print("Collecting live data for RSI filtering, no trading is executed")
                else:
                    print("Not enough data to apply strategy")
            
            # filter out stickers by RSI value
            if not self.rsi_filtered and len(self.stickers_to_delete) > 0:
                self.rsi_filter_stickers() 
                print(f"Sticker dictionary filtered by RSI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")       

        except Exception as e:
            print(str(e))
            
    def get_current_capital(self):
        return float(self.trading_client.get_account().cash)
    
    def get_previous_position(self, symbol):
        positions = self.trading_client.get_all_positions()
        if positions is not None and len(positions) > 0:
            for p in positions:
                if p.symbol == symbol:
                    return p.side.value
                else:
                    return POS_OUT
        else:
            return POS_OUT
        
    def execute_trading_action(self, symbol, current_df):
        trading_action = current_df.iloc[-1][TRADING_ACTION]
        current_position = current_df.iloc[-2][POSITION]

        # divide capital with amount of OUT positions:
        out_positions = self.data_generator.get_out_positions()
        quantity_buy_long = current_df.iloc[-1][CURRENT_CAPITAL] / out_positions / current_df.iloc[-1][CLOSE]

        #NOTE sell only a percentage of divided capital
        quantity_sell_short = (current_df.iloc[-1][CURRENT_CAPITAL] / out_positions * 0.15) / current_df.iloc[-1][CLOSE]

        if trading_action == ACT_BUY_NEXT_LONG and current_position == POS_OUT:
            self.place_buy_order(quantity_buy_long, symbol)
        elif trading_action == ACT_SELL_NEXT_SHORT and current_position == POS_OUT:
            self.place_sell_order(quantity_sell_short, symbol)
        elif trading_action == ACT_SELL_PREV_LONG and current_position == POS_LONG_BUY:
            self.close_current_position(position="Sell previous long", symbol=symbol)
        elif trading_action == ACT_BUY_PREV_SHORT and current_position == POS_SHORT_SELL:
            self.close_current_position(position="Buy previous long", symbol=symbol)
        else:
            print(ACT_NO_ACTION)

    def rsi_filter_stickers(self):
        for sticker in self.stickers_to_delete:
            del self.data_generator.sticker_dict[sticker]
        self.rsi_filtered = True
            
    def place_buy_order(self, quantity, symbol, price=None):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=quantity,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(order_data=market_order_data)
            self.data_generator.decrease_out_positions()
            print('Buy order completed')
        except Exception as e:
            print(str(e))

    def place_sell_order(self, quantity, symbol, price=None):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=round(quantity), #TODO: kell kerekítés?
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(order_data=market_order_data)
            self.data_generator.decrease_out_positions()
            print('Sell order completed')
        except Exception as e:
            print(str(e))

    def close_current_position(self, symbol, position=None, price=None):
        try:
            self.trading_client.close_position(symbol)
            self.data_generator.increase_out_positions()
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
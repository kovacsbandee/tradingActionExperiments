from datetime import datetime
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from src_tr.main.scanners.ScannerBase import ScannerBase
from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.helpers.converter import string_to_dict_list
from src_tr.main.enums_and_constants.trading_constants import *

class TradingManagerMain():

    def __init__(self, 
                #scanner: ScannerBase,
                #NOTE: 'recommended_sticker_list' kell majd
                data_generator: PriceDataGeneratorMain,
                strategy: StrategyWithStopLoss,
                trading_client: TradingClient,
                key: str,
                secret_key: str,
                #market_open: datetime,
                #market_close: datetime,
                symbol_list: list): #TODO: lista érkezik be
        #self.scanner = scanner
        self.data_generator = data_generator
        self.strategy = strategy
        self.trading_client = trading_client
        self.key = key
        self.secret_key = secret_key
        #self.market_open = market_open
        #self.market_close = market_close
        self.symbol_list = symbol_list

    def on_open(self, ws: websocket.WebSocketApp):
        print(f"WebSocket connection opened on URL: {ws.url}")
        self.data_generator.initialize_sticker_data()
        self.data_generator.initialize_sticker_dict()
        auth_data = {"action": "auth", "key": f"{self.key}", "secret": f"{self.secret_key}"}

        ws.send(json.dumps(auth_data))

        #NOTE: polygon -> {"action":"subscribe", "params":"AM.AAPL,AM.TSLA,AM.MSFT"}
        listen_message = {
            "action":"subscribe",
            "bars": [self.symbol_list] #TODO: lista lesz, nem kell a [] majd
            }

        ws.send(json.dumps(listen_message))
        
    def on_message(self, ws, message):
        try:
            print("New bar data received at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            minute_bars = string_to_dict_list(message)
            
            #TODO: for mb in minute_bars + lsd. TradingManagerDraft -> handle_message
            if minute_bars[0]['T'] == 'b':
                self.data_generator.update_sticker_df(minute_bars=minute_bars)
                
                sticker_df_length = len(self.data_generator.sticker_dict[self.symbol_list])
                str_ma_long_value = int(self.strategy.ma_long)
                if sticker_df_length > str_ma_long_value:
                    for key, value in self.data_generator.sticker_dict.values():
                        #implement
                        pass
                    self.strategy.set_sticker_df(self.data_generator.sticker_dict[self.symbol_list])
                    self.strategy.update_capital_amount(float(self.trading_client.get_account().cash))
                    self.strategy.apply_long_strategy(trading_client=self.trading_client, symbol=self.symbol_list)
                    
                    sticker_df = self.strategy.sticker_df

                    trading_action = sticker_df.iloc[-1][TRADING_ACTION]
                    current_position = sticker_df.iloc[-2][POSITION]
                    quantity_buy_long = sticker_df.iloc[-1][CURRENT_CAPITAL] / sticker_df.iloc[-1][CLOSE]
                    quantity_sell_short = 5000 / sticker_df.iloc[-1][CLOSE]

                    # kurvanagy TODO: 
                    if trading_action == ACT_BUY_NEXT_LONG and current_position == POS_OUT:
                        self.place_buy_order(quantity_buy_long)
                        # refresh position in sticker_df?
                    elif trading_action == ACT_SELL_NEXT_SHORT and current_position == POS_OUT:
                        self.place_sell_order(quantity_sell_short)
                        # refresh position in sticker_df?
                    elif trading_action == ACT_SELL_PREV_LONG and current_position == POS_LONG_BUY:
                        self.close_current_position("Sell previous long")
                    elif trading_action == ACT_BUY_PREV_SHORT and current_position == POS_SHORT_SELL:
                        self.close_current_position("Buy previous long")
                    else:
                        print(ACT_NO_ACTION)
                else:
                    print("Not enough data to apply strategy")
            else:
                print('Authentication and data initialization')
        except Exception as e:
            print(str(e))
            
    def place_buy_order(self, quantity):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=self.symbol_list,
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

    def place_sell_order(self, quantity):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=self.symbol_list,
                            qty=round(quantity),
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(
                            order_data=market_order_data
                        )
            print('Sell order completed')
        except Exception as e:
            print(str(e))

    def close_current_position(self, position):
        try:
            self.trading_client.close_position(self.symbol_list)
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
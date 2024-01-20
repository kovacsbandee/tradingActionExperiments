from datetime import datetime
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import pandas as pd

from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.strategies.StrategyWithStopLoss import StrategyWithStopLoss
from src_tr.main.helpers.converter import string_to_dict_list

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
        self.symbols_to_delete = []
        self.rsi_filtered = False
        self.rsi_counter = 0
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
                    if len(self.minute_bars) == len(self.data_generator.recommended_symbol_list):
                        self.execute_all()
                        self.minute_bars = []
                        print('Data available, execute() called')

            else:
                print('Authentication and data initialization')
        except Exception as e:
            print(str(e))

    def on_open(self, ws: websocket.WebSocketApp):
        print(f"WebSocket connection opened on URL: {ws.url}")
        self.data_generator.initialize_symbol_dict()
        auth_data = {"action": "auth", "key": f"{self.api_key}", "secret": f"{self.secret_key}"}

        ws.send(json.dumps(auth_data))

        #NOTE: polygon -> {"action":"subscribe", "params":"AM.AAPL,AM.TSLA,AM.MSFT"}
        listen_message = {
            "action":"subscribe",
            "bars": [s['symbol'] for s in self.data_generator.recommended_symbol_list]
            }

        ws.send(json.dumps(listen_message))
        
    def execute_all(self):
        try:
            self.data_generator.update_symbol_df(minute_bars=self.minute_bars)
            
            # apply strategy on all symbols
            self.apply_strategy()
            
            # filter out symbols by RSI value
            if not self.rsi_filtered and len(self.symbols_to_delete) > 0:
                self.rsi_filter_symbols() 
                print(f"Symbol dictionary filtered by RSI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            elif not self.rsi_filtered and self.rsi_counter == len(self.data_generator.recommended_symbol_list):
                self.rsi_filtered = True
                print(f"No RSI filtering required, trading cycle started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
                    return 'out'
        else:
            return 'out'
        
    def apply_strategy(self):
        for symbol, value_dict in self.data_generator.symbol_dict.items():
            # normalize open price
            value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'open_norm'] = \
            (value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'o'] - value_dict['prev_day_data']['avg_open']) / value_dict['prev_day_data']['std_open']
            
            symbol_df_length = len(value_dict['daily_price_data_df'])
            ma_long_value = self.strategy.ma_long
            if symbol_df_length > ma_long_value:
                current_capital = self.get_current_capital()
                self.strategy.update_capital_amount(current_capital)
                previous_position = self.get_previous_position(symbol)
                self.data_generator.symbol_dict[symbol] = self.strategy.apply_long_strategy(previous_position=previous_position, 
                                                                                                symbol=symbol,  
                                                                                                symbol_dict=value_dict)
                current_df: pd.DataFrame = value_dict['daily_price_data_df']
                if len(current_df) > self.minutes_before_trading_start:
                    if not self.rsi_filtered and current_df['rsi'].mean() < self.rsi_threshold: #NOTE: megfordítottam a >-t!
                        self.symbols_to_delete.append(symbol)
                    elif not self.rsi_filtered and current_df['rsi'].mean() >= self.rsi_threshold:
                        self.rsi_counter += 1
                    if self.rsi_filtered:
                        self.execute_trading_action(symbol, current_df)
                else:
                    print("Collecting live data for RSI filtering, no trading is executed")
            else:
                print(f"Not enough data to apply strategy. Symbol: {symbol}")
        
    def execute_trading_action(self, symbol, current_df):
        trading_action = current_df.iloc[-1]['trading_action']
        current_position = current_df.iloc[-2]['position']

        # divide capital with amount of OUT positions:
        out_positions = self.data_generator.get_out_positions()
        quantity_buy_long = current_df.iloc[-1]['current_capital'] / out_positions / current_df.iloc[-1]['o']

        #NOTE sell only a percentage of divided capital
        quantity_sell_short = (current_df.iloc[-1]['current_capital'] / out_positions * 0.15) / current_df.iloc[-1]['o']

        if trading_action == 'buy_next_long_position' and current_position == 'out':
            self.place_buy_order(quantity_buy_long, symbol)
        elif trading_action == 'sell_next_short_position' and current_position == 'out':
            self.place_sell_order(quantity_sell_short, symbol)
        elif trading_action == 'sell_previous_long_position' and current_position == 'long':
            self.close_current_position(position="Sell previous long", symbol=symbol)
        elif trading_action == 'buy_previous_short_position' and current_position == 'short':
            self.close_current_position(position="Buy previous long", symbol=symbol)
        else:
            print('no_action')

    def rsi_filter_symbols(self):
        for symbol in self.symbols_to_delete:
            del self.data_generator.symbol_dict[symbol]
        self.rsi_filtered = True
            
    def place_buy_order(self, quantity, symbol, price=None):
        try:
            # https://alpaca.markets/learn/13-order-types-you-should-know-about/
            # a link szerint a time_in_force-nak inkább 'ioc'-nak kéne lennie szerintem.
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
        # Ide bele kell tenni a daily_price_data_df ábrázolását!
        print(f"Connection closed with status code {close_status_code}: {close_msg}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
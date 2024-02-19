from datetime import datetime
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import pandas as pd
import traceback

from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmMain import TradingAlgorithmMain
from src_tr.main.utils.converter import string_to_dict_list

class TradingManagerMain():

    def __init__(self,
                data_generator: PriceDataGeneratorMain,
                trading_algorithm: TradingAlgorithmMain,
                algo_params: dict,
                trading_client: TradingClient,
                api_key: str,
                secret_key: str
                ):
        self.data_generator = data_generator
        self.trading_algorithm = trading_algorithm
        self.algo_params=algo_params
        self.trading_client = trading_client
        self.api_key = api_key
        self.secret_key = secret_key
        self.minute_bars = []

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
        except:
            traceback.print_exc()

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
            self.apply_trading_algorithm()
        except:
            traceback.print_exc()
            
    def get_current_capital(self):
        return float(self.trading_client.get_account().cash)
    
    def _normalize_open_price(self, value_dict):
        value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'open_norm'] = \
                (value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'o']\
                    - value_dict['prev_day_data']['avg_open']) / value_dict['prev_day_data']['std_open']
        return value_dict
                
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
        
    def apply_trading_algorithm(self):
        for symbol, value_dict in self.data_generator.symbol_dict.items():
            if self.algo_params["entry_signal"] == "default":
                value_dict = self._normalize_open_price(value_dict)
            
            symbol_df_length = len(value_dict['daily_price_data_df'])
            ma_long_value = self.algo_params["entry_windows"]["long"]
            if symbol_df_length > ma_long_value:
                current_capital = self.get_current_capital()
                self.trading_algorithm.update_capital_amount(current_capital)
                previous_position = self.get_previous_position(symbol)
                self.data_generator.symbol_dict[symbol] = \
                    self.trading_algorithm.apply_long_trading_algorithm(previous_position=previous_position, 
                                                                        symbol=symbol,  
                                                                        symbol_dict=value_dict,
                                                                        algo_params=self.algo_params)
                current_df = value_dict['daily_price_data_df']
                self.execute_trading_action(symbol, current_df)
            else:
                print(f"Collecting data...[symbol: {symbol}, remaining: {ma_long_value-symbol_df_length}min]")
        
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
            
    def place_buy_order(self, quantity, symbol, price=None):
        try:
            # https://alpaca.markets/learn/13-order-types-you-should-know-about/
            # a link szerint a time_in_force-nak inkább 'ioc'-nak kéne lennie szerintem.
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=quantity,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.IOC
                            )
            self.trading_client.submit_order(order_data=market_order_data)
            self.data_generator.decrease_out_positions()
            print('Buy order completed')
        except:
            traceback.print_exc()

    def place_sell_order(self, quantity, symbol, price=None):
        try:
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=round(quantity),
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(order_data=market_order_data)
            self.data_generator.decrease_out_positions()
            print('Sell order completed')
        except:
            traceback.print_exc()

    def close_current_position(self, symbol, position=None, price=None):
        try:
            self.trading_client.close_position(symbol)
            self.data_generator.increase_out_positions()
            print(f'{position} position closed successfully')
        except:
            traceback.print_exc()
        
    def on_ping(self, ws, ping_payload):
        print(f"Ping sent: {ping_payload}")
        
    def on_pong(self, ws, pong_payload):
        print(f"Pong received: {pong_payload}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed with status code {close_status_code}: {close_msg}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
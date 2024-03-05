from datetime import datetime
import websocket, json
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import traceback

from src_tr.main.data_generators.PriceDataGeneratorMain import PriceDataGeneratorMain
from src_tr.main.trading_algorithms.TradingAlgorithmMain import TradingAlgorithmMain

class TradingManagerMain():

    def __init__(self,
                data_generator: PriceDataGeneratorMain,
                trading_algorithm: TradingAlgorithmMain,
                algo_params: dict,
                trading_client: TradingClient,
                api_key: str,
                secret_key: str,
                ws_close_func=None
                ):
        self.data_generator = data_generator
        self.trading_algorithm = trading_algorithm
        self.algo_params=algo_params
        self.trading_client = trading_client
        self.api_key = api_key
        self.secret_key = secret_key
        self.minute_bars = []
        self.ws_close_func = ws_close_func

    def handle_message(self, ws, message):
        if datetime.now().strftime("%H:%M") == "21:00":
            self.ws_close_func()
        else:
            try:
                minute_bars = self._parse_json(message)
                print("\nData received")
                print(f"\t[Time: {datetime.now()}]")
                print(f"\t[Message: {minute_bars}]\n")
                if minute_bars[0]['T'] == 'b':
                    for item in minute_bars: #TODO: máshogy kell kezelni azt, hogy nem egyszerre érkezik be minden részvényhez az adat
                        self.minute_bars.append(item)
                        print(f"\nBar data added to TradingManager.minute_bars")
                        print(f"\t[Time: {datetime.now()}]")
                        print(f"\t[TradingManager.minute_bars: {self.minute_bars}]\n")
                        if len(self.minute_bars) == len(self.data_generator.recommended_symbol_list):
                            print(f"\nData available for all symbols")
                            print(f"\t[Time: {datetime.now()}]\n \t[TradingManager.minute_bars: {self.minute_bars}]")                        
                            self.execute_all()
                            self.minute_bars = []
                else:
                    print('Authentication and data initialization')
            except:
                traceback.print_exc()
            
    def _parse_json(self, json_string):
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
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
        
<<<<<<< Updated upstream
    def execute_all(self):
        try:
            print(f"\nUpdating DataGenerator.symbol_df\n \t[Time: {datetime.now()}]")
            self.data_generator.update_symbol_df(minute_bars=self.minute_bars)
            print(f"\nUpdated DataGenerator.symbol_df\n \t[Time: {datetime.now()}]")
            
            print(f"\nCalling TradingManager.apply_trading_algorithm()\n \t[Time: {datetime.now()}]")
            self.apply_trading_algorithm()
            print(f"\nFinished TradingManager.apply_trading_algorithm()\n \t[Time: {datetime.now()}]")
=======
    def execute_all(self, current_time: datetime):
        try:
            if self.minute_bars is not None and len(self.minute_bars) > 0:
                for bar in self.minute_bars:
                    symbol = bar['S']
                    current_bar_df = pd.DataFrame([bar])
                    current_bar_df['t'] = pd.DatetimeIndex(pd.to_datetime(current_bar_df['t']))
                    current_bar_df.set_index('t', inplace=True)
                    
                    current_bar_minute = current_bar_df.index[-1].minute

                    if self.symbol_dict[symbol]['daily_price_data_df'] is None:
                        self.symbol_dict[symbol]['daily_price_data_df'] = current_bar_df
                        self.initialize_additional_columns(symbol)
                    elif isinstance(self.symbol_dict[symbol]['daily_price_data_df'], pd.DataFrame):
                        latest_bar_minute = self.symbol_dict[symbol]['daily_price_data_df'].index[-1].minute
                        case_consequent = current_bar_minute == (current_time-timedelta(minutes=1)).minute \
                                            and latest_bar_minute == (current_time-timedelta(minutes=2)).minute
                        case_non_consequent = current_bar_minute == (current_time-timedelta(minutes=1)).minute \
                                                and latest_bar_minute < (current_time-timedelta(minutes=2)).minute
                        if case_consequent:
                            self.symbol_dict[symbol]['daily_price_data_df'] = \
                                pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], current_bar_df])
                            self.apply_trading_algorithm(symbol, self.symbol_dict[symbol])
                        elif case_non_consequent:
                            delay = (current_bar_df.index[-1] - timedelta(minutes=latest_bar_minute)).minute                                
                            while delay > 1:
                                new_row: pd.DataFrame = self.symbol_dict[symbol]['daily_price_data_df'].iloc[-1:].copy()
                                new_row.index = new_row.index + timedelta(minutes=1)
                                new_row.loc[new_row.index[-1], 'trading_action'] = 'no_action'
                                new_row.loc[new_row.index[-1], 'entry_signal_type'] = None
                                new_row.loc[new_row.index[-1], 'close_signal_type'] = None
                                new_row.loc[new_row.index[-1], 'data_correction'] = 'corrected'
                                self.symbol_dict[symbol]['daily_price_data_df'] = \
                                    pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], new_row])
                                self.symbol_dict[symbol]['daily_price_data_df'] = \
                                    self.symbol_dict[symbol]['daily_price_data_df'].sort_index()
                                delay-=1
                            self.symbol_dict[symbol]['daily_price_data_df'] = pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], current_bar_df])
                            self.apply_trading_algorithm(symbol, self.symbol_dict[symbol])
                    else:
                        raise ValueError("Unexpected data structure for the symbol in current_data_window")
            else:
                raise ValueError("Minute bar list is empty.")
>>>>>>> Stashed changes
        except:
            traceback.print_exc()
            
    def get_current_capital(self):
        return float(self.trading_client.get_account().cash)
    
    def _normalize_open_price(self, value_dict):
        value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'open_norm'] = \
                (value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'o']\
                    - value_dict['prev_day_data']['avg_open']) / value_dict['prev_day_data']['std_open']
        return value_dict
                
    def get_previous_positions(self):
        pos_dict = dict()
        for item in self.data_generator.recommended_symbol_list:
            pos_dict[item['symbol']] = 'out'
        positions = self.trading_client.get_all_positions()
        if positions is not None and len(positions) > 0:
            for p in positions:
                pos_dict[p.symbol] = p.side.value
        return pos_dict
        
    def apply_trading_algorithm(self):
        positions_by_symbol = self.get_previous_positions()
        for symbol, symbol_dict in self.data_generator.symbol_dict.items():
            if self.algo_params["entry_signal"] == "default":
                symbol_dict = self._normalize_open_price(symbol_dict)
            
            symbol_df_length = len(symbol_dict['daily_price_data_df']) if symbol_dict['daily_price_data_df'] is not None else 0
            ma_long_value = self.algo_params["entry_windows"]["long"]
            if symbol_df_length > ma_long_value:
                current_capital = self.get_current_capital()
                self.trading_algorithm.update_capital_amount(current_capital)
                previous_position = positions_by_symbol[symbol]
                symbol_dict = \
                    self.trading_algorithm.apply_long_trading_algorithm(previous_position=previous_position, 
                                                                        symbol=symbol,  
                                                                        symbol_dict=symbol_dict,
                                                                        algo_params=self.algo_params)
                self.execute_trading_action(symbol=symbol, current_df=symbol_dict['daily_price_data_df'])
            else:
                print(f"Collecting data...[symbol: {symbol}, remaining: {ma_long_value-symbol_df_length}min]")
        
    def execute_trading_action(self, symbol, current_df):
        trading_action = current_df.iloc[-1]['trading_action']
        current_position = current_df.iloc[-2]['position']

        # divide capital with amount of OUT positions:
        out_positions = self.data_generator.get_out_positions()
        try:
            quantity_buy_long = current_df.iloc[-1]['current_capital'] / out_positions / current_df.iloc[-1]['o']
        except:
            traceback.print_exc()
            
        if trading_action == 'buy_next_long_position': # and current_position == 'out':
            print(f"Initiating long position for {symbol} at {datetime.now()}")
            self.place_buy_order(quantity_buy_long, symbol)
        elif trading_action == 'sell_previous_long_position': # and current_position == 'long':
            print(f"Initiating position close for {symbol} at {datetime.now()}")
            self.close_current_position(position="Sell previous long", symbol=symbol)
        else:
            print(f'No action on {symbol} [{datetime.now()}]')
            
    def place_buy_order(self, quantity, symbol, price=None):
        try:
            # https://alpaca.markets/learn/13-order-types-you-should-know-about/
            # a link szerint a time_in_force-nak inkább 'ioc'-nak kéne lennie szerintem.
            # KT NOTE: az IOC-val nem lehet törtrészvényt vásárolni?
            market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=quantity,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY
                            )
            self.trading_client.submit_order(order_data=market_order_data)
            self.data_generator.decrease_out_positions()
            print(f'Buy order completed\n \t[Symbol:{symbol}]\n \t[Time:{datetime.now()}]\n \t[Quantity: {quantity}]')
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
            print(f'{position} position closed successfully\n \t[Symbol:{symbol}\n \tTime:{datetime.now()}]')
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
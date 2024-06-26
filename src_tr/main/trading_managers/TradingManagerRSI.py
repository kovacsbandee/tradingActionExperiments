from datetime import datetime
import pandas as pd

from .TradingManagerMain import TradingManagerMain

class TradingManagerRSI(TradingManagerMain):
    
    def __init__(self, 
                 rsi_threshold: int,
                 minutes_before_trading_start: int):
        super().__init__()
        self.rsi_filtered = False
        self.rsi_counter = 0
        self.rsi_threshold = rsi_threshold
        self.minutes_before_trading_start = minutes_before_trading_start
        self.symbols_to_delete = []
        
    def execute_all(self):
        try:
            self.data_generator.update_symbol_df(minute_bars=self.minute_bars)
            
            # apply trading algorithm on all symbols
            self.apply_trading_algorithm()
            
            # filter out symbols by RSI value
            if not self.rsi_filtered and len(self.symbols_to_delete) > 0:
                self.rsi_filter_symbols() 
                print(f"Symbol dictionary filtered by RSI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            elif not self.rsi_filtered and self.rsi_counter == len(self.data_generator.recommended_symbol_list):
                self.rsi_filtered = True
                print(f"No RSI filtering required, trading cycle started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(str(e))
    
    def apply_trading_algorithm(self):
        for symbol, value_dict in self.data_generator.symbol_dict.items():
            # normalize open price
            value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'open_norm'] = \
            (value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'o'] - value_dict['prev_day_data']['avg_open']) \
                / value_dict['prev_day_data']['std_open']
            
            symbol_df_length = len(value_dict['daily_price_data_df'])
            ma_long_value = self.algo_params["entry_windows"]["long"]
            if symbol_df_length > ma_long_value:
                current_capital = self.get_current_capital()
                self.trading_algorithm.update_capital_amount(current_capital)
                previous_position = self.get_previous_positions(symbol)
                self.data_generator.symbol_dict[symbol] = self.trading_algorithm.apply_long_trading_algorithm(previous_position=previous_position, 
                                                                                                symbol=symbol,  
                                                                                                symbol_dict=value_dict,
                                                                                                algo_params=self.algo_params)
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
                print(f"Not enough data to apply trading algorithm. Symbol: {symbol}")
                
    def rsi_filter_symbols(self):
        for symbol in self.symbols_to_delete:
            del self.data_generator.symbol_dict[symbol]
        self.rsi_filtered = True
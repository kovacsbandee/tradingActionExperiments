import pandas as pd

from .TestTradingManager import TestTradingManager
from .TestTradingClientDivided import TestTradingClientDivided

class TestTradingManagerDivided(TestTradingManager):
    
    #Override    
    def get_current_capital(self, symbol):
        if isinstance(self.trading_client, TestTradingClientDivided):
            return float(self.trading_client.get_max_cash_by_symbol(symbol))
        else:
            raise Exception("trading_client is not instance of TestTradingClientDivided")
    
    #Override
    def apply_trading_algorithm(self):
        for symbol, value_dict in self.data_generator.symbol_dict.items():
            # normalize open price
            value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'open_norm'] = \
            (value_dict['daily_price_data_df'].loc[value_dict['daily_price_data_df'].index[-1], 'o'] - value_dict['prev_day_data']['avg_open']) / value_dict['prev_day_data']['std_open']
            
            SYMBOL_DF_length = len(value_dict['daily_price_data_df'])
            ma_long_value = self.trading_algorithm.ma_long
            if SYMBOL_DF_length > ma_long_value:
                current_capital = self.get_current_capital(symbol)
                self.trading_algorithm.update_capital_amount(current_capital)
                previous_position = self.get_previous_position(symbol)
                self.data_generator.symbol_dict[symbol] = self.trading_algorithm.apply_long_trading_algorithm(previous_position=previous_position, 
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
                print(f"Not enough data to apply trading_algorithm. Symbol: {symbol}")
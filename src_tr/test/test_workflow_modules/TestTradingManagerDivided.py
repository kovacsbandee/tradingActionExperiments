import pandas as pd

from src_tr.main.enums_and_constants.trading_constants import *
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
    def apply_strategy(self):
        for symbol, value_dict in self.data_generator.symbol_dict.items():
            # normalize open price
            value_dict[SYMBOL_DF].loc[value_dict[SYMBOL_DF].index[-1], OPEN_NORM] = \
            (value_dict[SYMBOL_DF].loc[value_dict[SYMBOL_DF].index[-1], OPEN] - value_dict[PREV_DAY_DATA][AVG_OPEN]) / value_dict[PREV_DAY_DATA][STD_OPEN]
            
            SYMBOL_DF_length = len(value_dict[SYMBOL_DF])
            ma_long_value = self.strategy.ma_long
            if SYMBOL_DF_length > ma_long_value:
                current_capital = self.get_current_capital(symbol)
                self.strategy.update_capital_amount(current_capital)
                previous_position = self.get_previous_position(symbol)
                self.data_generator.symbol_dict[symbol] = self.strategy.apply_long_strategy(previous_position=previous_position, 
                                                                                                symbol=symbol,  
                                                                                                symbol_dict=value_dict)
                current_df: pd.DataFrame = value_dict[SYMBOL_DF]
                if len(current_df) > self.minutes_before_trading_start:
                    if not self.rsi_filtered and current_df[RSI].mean() < self.rsi_threshold: #NOTE: megfordítottam a >-t!
                        self.symbols_to_delete.append(symbol)
                    elif not self.rsi_filtered and current_df[RSI].mean() >= self.rsi_threshold:
                        self.rsi_counter += 1
                    if self.rsi_filtered:
                        self.execute_trading_action(symbol, current_df)
                else:
                    print("Collecting live data for RSI filtering, no trading is executed")
            else:
                print(f"Not enough data to apply strategy. Symbol: {symbol}")
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
            if self.algo_params["entry_signal"] == "default":
                value_dict = self._normalize_open_price(value_dict)
                
            symbol_df_length = len(value_dict['daily_price_data_df'])
            ma_long_value = self.algo_params["entry_windows"]["long"]
            if symbol_df_length > ma_long_value:
                current_capital = self.get_current_capital(symbol)
                self.trading_algorithm.update_capital_amount(current_capital)
                previous_position = self.get_previous_positions(symbol)
                self.data_generator.symbol_dict[symbol] = \
                    self.trading_algorithm.apply_long_trading_algorithm(previous_position=previous_position, 
                                                                        symbol=symbol,  
                                                                        symbol_dict=value_dict,
                                                                        algo_params=self.algo_params)
                current_df = value_dict['daily_price_data_df']
                self.execute_trading_action(symbol, current_df)
            else:
                print(f"Collecting data...[symbol: {symbol}, remaining: {ma_long_value-symbol_df_length}min]")
                
    #Override
    def execute_trading_action(self, symbol, current_df):
        trading_action = current_df.iloc[-1]['trading_action']
        current_position = current_df.iloc[-2]['position']

        quantity_buy_long = current_df.iloc[-1]['current_capital'] / current_df.iloc[-1]['o']

        if trading_action == 'buy_next_long_position' and current_position == 'out':
            self.place_buy_order(symbol=symbol, quantity=quantity_buy_long, price=current_df.iloc[-1]['o'])
        elif trading_action == 'sell_previous_long_position' and current_position == 'long':
            self.close_current_position(symbol=symbol, price=current_df.iloc[-1]['o'])
        else:
            print('no_action')

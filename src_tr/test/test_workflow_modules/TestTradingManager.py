import pandas as pd
from typing import List
import traceback

from src_tr.main.trading_managers.TradingManagerMain import TradingManagerMain

class TestTradingManager(TradingManagerMain):
    
    #Override
    def handle_message(self, ws, message: List[dict]):
        try:
            for item in message:
                self.minute_bars.append(item)
                if len(self.minute_bars) == len(self.data_generator.recommended_symbol_list):
                    self.execute_all()
                    self.minute_bars = []
        except:
            traceback.print_exc()

    #Override
    def on_open(self, ws):
        self.data_generator.initialize_symbol_dict()
        print(f"Symbol dict initialized:\n {self.data_generator.symbol_dict}")
    
    #Override    
    def get_current_capital(self):
        return float(self.trading_client.cash)
    
    #Override
    def get_previous_position(self, symbol):
        return self.trading_client.get_position_by_symbol(symbol)
    
    #Override
    def execute_trading_action(self, symbol, current_df):
        trading_action = current_df.iloc[-1]['trading_action']
        current_position = current_df.iloc[-2]['position']

        # divide capital with amount of OUT positions:
        out_positions = self.data_generator.get_out_positions()
        quantity_buy_long = current_df.iloc[-1]['current_capital'] / out_positions / current_df.iloc[-1]['o']

        if trading_action == 'buy_next_long_position' and current_position == 'out':
            self.place_buy_order(symbol=symbol, quantity=quantity_buy_long, price=current_df.iloc[-1]['o'])
        elif trading_action == 'sell_previous_long_position' and current_position == 'long':
            self.close_current_position(symbol=symbol, price=current_df.iloc[-1]['o'])
        else:
            print('no_action')
            
    #Override
    def place_buy_order(self, quantity, symbol, price=None):
        try:
            self.trading_client.submit_order(symbol=symbol, qty=quantity, price=price)
            self.data_generator.decrease_out_positions()
        except:
            traceback.print_exc()
            
    #Override
    def close_current_position(self, symbol, position=None, price=None):
        try:
            self.trading_client.close_position(symbol, price)
            self.data_generator.increase_out_positions()
        except:
            traceback.print_exc()
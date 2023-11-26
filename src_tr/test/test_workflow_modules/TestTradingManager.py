import pandas as pd
from typing import List

from src_tr.main.trading_managers.TradingManagerMain import TradingManagerMain
from src_tr.main.helpers.converter import string_to_dict_list
from src_tr.main.enums_and_constants.trading_constants import *

class TestTradingManager(TradingManagerMain):
    
    #Override
    def handle_message(self, ws, message: List[dict]):
        try:
            for item in message:
                self.minute_bars.append(item)
                if len(self.minute_bars) == len(self.data_generator.recommended_sticker_list):
                    self.execute_all()
                    self.minute_bars = []
        except Exception as e:
            print(str(e))

    #Override
    def on_open(self, ws):
        self.data_generator.initialize_sticker_dict()
        print(f"Sticker dict initialized:\n {self.data_generator.sticker_dict}")
    
    #Override    
    def get_current_capital(self):
        return float(self.trading_client.cash)
    
    #Override
    def get_previous_position(self, symbol):
        return self.trading_client.get_position_by_symbol(symbol)
    
    #Override
    def execute_trading_action(self, symbol, current_df):
        trading_action = current_df.iloc[-1][TRADING_ACTION]
        current_position = current_df.iloc[-2][POSITION]

        # divide capital with amount of OUT positions:
        out_positions = self.data_generator.get_out_positions()
        quantity_buy_long = current_df.iloc[-1][CURRENT_CAPITAL] / out_positions / current_df.iloc[-1][OPEN]

        if trading_action == ACT_BUY_NEXT_LONG and current_position == POS_OUT:
            self.place_buy_order(symbol=symbol, quantity=quantity_buy_long, price=current_df.iloc[-1][OPEN])
        elif trading_action == ACT_SELL_PREV_LONG and current_position == POS_LONG_BUY:
            self.close_current_position(symbol=symbol, price=current_df.iloc[-1][OPEN])
        else:
            print(ACT_NO_ACTION)
            
    #Override
    def place_buy_order(self, quantity, symbol, price=None):
        try:
            self.trading_client.submit_order(symbol=symbol, qty=quantity, price=price)
            self.data_generator.decrease_out_positions()
        except Exception as e:
            print(str(e))
            
    #Override
    def close_current_position(self, symbol, position=None, price=None):
        try:
            self.trading_client.close_position(symbol, price)
            self.data_generator.increase_out_positions()
        except Exception as e:
            print(str(e))
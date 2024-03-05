from typing import List
import pandas as pd
from pandas import DataFrame
from datetime import datetime, timedelta
import pytz

class PriceDataGeneratorMain():

    def __init__(self, recommended_symbol_list):
        self.out_positions = len(recommended_symbol_list)
        self.recommended_symbol_list =  recommended_symbol_list
        self.symbol_dict = dict()

    def get_out_positions(self):
        return self.out_positions

    def increase_out_positions(self):
        self.out_positions = self.out_positions + 1

    def decrease_out_positions(self):
        self.out_positions = self.out_positions - 1

    def initialize_symbol_dict(self):
        if self.recommended_symbol_list is not None:
            for e in self.recommended_symbol_list:
                self.symbol_dict[e['symbol']] = {
                    'daily_price_data_df' : None,
                    'previous_long_buy_position_index' : None,
                    'previous_short_sell_position_index' : None,
                    'indicator_price' : 'o',
                    'prev_day_data' : {
                        'avg_open' : e['avg_open'],
                        'std_open': e['std_open']
                    }
                }
        else:
            raise ValueError("Recommended symbol list is empty.")
        
    def initialize_additional_columns(self, symbol):
        self.symbol_dict[symbol]['daily_price_data_df']['position'] = 'out'
        self.symbol_dict[symbol]['daily_price_data_df']['trading_action'] = 'no_action'
        self.symbol_dict[symbol]['daily_price_data_df']['current_capital'] = 0.0
        self.symbol_dict[symbol]['daily_price_data_df']['entry_signal_type'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['close_signal_type'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['rsi'] = None
        self.symbol_dict[symbol]['daily_price_data_df']["close_signal_avg"] = None
        self.symbol_dict[symbol]['daily_price_data_df']['gain_loss'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['gain'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['loss'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['avg_gain'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['avg_loss'] = None
                
    def update_symbol_df(self, minute_bars: List[dict]):
        if minute_bars is not None and len(minute_bars) > 0:
            current_time = datetime.now(pytz.timezone("UTC")) #NOTE: ez kívülről jöjjön, hogy a tesztek is működhessenek
            for bar in minute_bars:
                symbol = bar['S']
                current_bar_df = DataFrame([bar])
                current_bar_df.set_index('t', inplace=True)

                if self.symbol_dict[symbol]['daily_price_data_df'] is None:
                    self.symbol_dict[symbol]['daily_price_data_df'] = current_bar_df
                    self.initialize_additional_columns(symbol)
                elif isinstance(self.symbol_dict[symbol]['daily_price_data_df'], DataFrame):
                    if current_bar_df.index[-1].minute == (current_time-timedelta(minutes=1)).minute \
                        and self.symbol_dict[symbol]['daily_price_data_df'].index[-1].minute == (current_time-timedelta(minutes=2)).minute:
                        self.symbol_dict[symbol]['daily_price_data_df'] = pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], current_bar_df])
                        #TODO: apply_algo()
                    elif current_bar_df.index[-1].minute == (current_time-timedelta(minutes=1)).minute \
                        and self.symbol_dict[symbol]['daily_price_data_df'].index[-1].minute > (current_time-timedelta(minutes=2)).minute:
                        delay = current_bar_df.index[-1].minute - self.symbol_dict[symbol]['daily_price_data_df'].index[-1].minute - timedelta(minutes=1)
                        while delay > 0:
                            new_row = self.symbol_dict[symbol]['daily_price_data_df'].iloc[-1:].copy()
                            new_row.index = new_row.index + timedelta(minutes=1)
                            self.symbol_dict[symbol]['daily_price_data_df'] = pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], new_row])
                            self.symbol_dict[symbol]['daily_price_data_df'] = self.symbol_dict[symbol]['daily_price_data_df'].sort_index()
                            delay-=1
                        self.symbol_dict[symbol]['daily_price_data_df'] = pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], current_bar_df])
                        # TODO: apply_algo()
                else:
                    raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Minute bar list is empty.")
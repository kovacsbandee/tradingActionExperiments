from typing import List
from datetime import datetime, timedelta
import pandas as pd
from pandas import DataFrame

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

    def update_symbol_df_of_symbol(self, bar):
        symbol = bar['S']
        bar_df = DataFrame([bar])
        bar_df.set_index('t', inplace=True)

        # padding
        daily_df = self.symbol_dict[symbol]['daily_price_data_df']
        if (isinstance(daily_df, DataFrame)):
            previous_bar = daily_df.iloc[-1]
            previous_datetime = datetime.strptime(daily_df.index[-1], "%Y-%m-%dT%H:%M:%SZ")
            current_datetime = datetime.strptime(bar['t'], "%Y-%m-%dT%H:%M:%SZ")

            while (current_datetime - previous_datetime).total_seconds() > 60:
                previous_datetime = previous_datetime + timedelta(minutes=1) # step previous_datetime with 1min
                padded_timestamp = previous_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

                padded_bar = previous_bar.copy()
                padded_bar.rename(padded_timestamp, inplace=True)
                
                constant_price = padded_bar.c
                padded_bar.o = constant_price
                padded_bar.h = constant_price
                padded_bar.l = constant_price
                padded_bar.vw = constant_price

                padded_bar.v = 1 # TODO - jó így?
                padded_bar.n = 1 # TODO - jó így?
                
                self.symbol_dict[symbol]['daily_price_data_df'].loc[padded_timestamp] = padded_bar
                print(f"\t\tPadded bar data for symbol {symbol} is added at timestamp {padded_timestamp}")
                # print(padded_bar)

                previous_bar = padded_bar

        if daily_df is None:
            self.symbol_dict[symbol]['daily_price_data_df'] = bar_df
            self.initialize_additional_columns(symbol)
        elif isinstance(daily_df, DataFrame):
            self.symbol_dict[symbol]['daily_price_data_df'] = pd.concat([daily_df, bar_df])
        else:
            raise ValueError("Unexpected data structure for the symbol in current_data_window")
    
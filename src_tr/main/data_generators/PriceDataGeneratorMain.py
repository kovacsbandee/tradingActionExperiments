from typing import List
import pandas as pd
from pandas import DataFrame

class PriceDataGeneratorMain():

    def __init__(self, recommended_symbol_list):
        self.ind_price = 'o'
        self.out_positions = len(recommended_symbol_list)
        #self.trading_day = trading_day
        self.recommended_symbol_list =  recommended_symbol_list
        self.symbol_dict = dict()

    def get_out_positions(self):
        return self.out_positions

    def increase_out_positions(self):
        self.out_positions = self.out_positions + 1

    def decrease_out_positions(self):
        self.out_positions = self.out_positions - 1

    # Mi lenne ha nem lenne külön symbol_list és symbol_dict?
    # hanem csak egy adattároló, amit elkezdünk feltölteni először a premarket scanner-rel,
    # utána folytatjuk a kereskedés inicializálással, gyakorlatilag evvel ami itt van,
    # majd folyamatosan töltjük a bejövő adatokkal és a pozíciókkal,
    # a végén pedig jó lenne kimenteni (valami olyan adatbázisba, amit mindenki elér) mindent, hogy utána lehessen rajtuk elemzéseket végezni
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
        self.symbol_dict[symbol]['daily_price_data_df']['current_capital'] = 0.0 #TODO: check!
        self.symbol_dict[symbol]['daily_price_data_df']['stop_loss_out_signal'] = 'no_stop_loss_out_signal'
        self.symbol_dict[symbol]['daily_price_data_df']['rsi'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['open_small_indicator'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['open_big_indicator'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['open_norm'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['gain_loss'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['gain'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['loss'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['avg_gain'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['avg_loss'] = None
        
        self.symbol_dict[symbol]['daily_price_data_df']['current_range'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['atr_short'] = None
        self.symbol_dict[symbol]['daily_price_data_df']['stop_loss_ma_short'] = None
        #-----TODO-----
        # Mi az AMOUNT_SOLD és az AMOUNT_BOUGHT definíciója? Mit értünk alattuk?
        #self.symbol_dict[symbol]['daily_price_data_df']['amount_sold'] = None
        #self.symbol_dict[symbol]['daily_price_data_df']['amount_bought'] = None
                
    def update_symbol_df(self, minute_bars: List[dict]):
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:
                symbol = bar['S']
                bar_df = DataFrame([bar])
                bar_df.set_index('t', inplace=True)

                if self.symbol_dict[symbol]['daily_price_data_df'] is None:
                    self.symbol_dict[symbol]['daily_price_data_df'] = bar_df
                    self.initialize_additional_columns(symbol)
                elif isinstance(self.symbol_dict[symbol]['daily_price_data_df'], DataFrame):
                    self.symbol_dict[symbol]['daily_price_data_df'] = pd.concat([self.symbol_dict[symbol]['daily_price_data_df'], bar_df])
                else:
                    raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Minute bar list is empty.")

    # Ezt hol használjuk és mire való?
    def update_symbol_df_yahoo(self, minute_bars: DataFrame):
        if minute_bars is not None and len(minute_bars) > 0:
            symbol = minute_bars['S'][0]
            #minute_bars.set_index('t', inplace=True)
            if self.symbol_dict[symbol] is None:
                self.symbol_dict[symbol] = minute_bars
            elif isinstance(self.symbol_dict[symbol], DataFrame):
                self.symbol_dict[symbol] = pd.concat([self.symbol_dict[symbol], minute_bars])
            else:
                raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Yahoo data is empty.")
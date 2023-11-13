from typing import List
from .PriceDataGeneratorBase import PriceDataGeneratorBase
import pandas as pd
from pandas import DataFrame

class PriceDataGeneratorMain(PriceDataGeneratorBase):

    def __init__(self, 
                 recommended_sticker_list
                 ):
        super().__init__(
                        recommended_sticker_list
                        )
    
    def initialize_sticker_dict(self):
        #self.sticker_data['trading_day'] = self.trading_day.strftime('%Y-%m-%d')
        self.sticker_data['stickers'] = dict()
        if self.recommended_sticker_list is not None:
            for stckr in self.recommended_sticker_list:
                self.sticker_data['stickers'][stckr] = dict()
                self.sticker_data['stickers'][stckr]['trading_day_data'] = None
                self.sticker_data['stickers'][stckr]['trading_day_sticker_stats'] = None
        else:
            raise ValueError("Recommended sticker list is empty.")
                
    def initialize_sticker_df(self):
        if self.recommended_sticker_list is not None:
            for stckr in self.recommended_sticker_list:
                self.sticker_df[stckr] = None
        else:
            raise ValueError("Recommended sticker list is empty.")
                
    def update_sticker_df(self, minute_bars: List[dict]):
        #TODO: ne vegyük el az első sort, ne legyen data_window size és legyen benne pozíció oszlop
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:
                symbol = bar['S']
                bar_df = DataFrame([bar])
                bar_df.set_index('t', inplace=True)

                if self.sticker_df[symbol] is None:
                    self.sticker_df[symbol] = bar_df
                elif isinstance(self.sticker_df[symbol], DataFrame):
                    self.sticker_df[symbol] = pd.concat([self.sticker_df[symbol], bar_df])
                else:
                    raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Minute bar list is empty.")
        
    def update_sticker_df_yahoo(self, minute_bars: DataFrame):
        if minute_bars is not None and len(minute_bars) > 0:
            symbol = minute_bars['S'][0]
            #minute_bars.set_index('t', inplace=True)
            if self.sticker_df[symbol] is None:
                self.sticker_df[symbol] = minute_bars
            elif isinstance(self.sticker_df[symbol], DataFrame):
                self.sticker_df[symbol] = pd.concat([self.sticker_df[symbol], minute_bars])
            else:
                raise ValueError("Unexpected data structure for the symbol in current_data_window")
        else:
            raise ValueError("Yahoo data is empty.")
                            
    def load_watchlist_daily_price_data(self):
        if self.recommended_sticker_list is not None:
            for symbol in self.recommended_sticker_list:

                avg_close = self.sticker_df[symbol]["c"].mean()
                avg_volume = self.sticker_df[symbol]["v"].mean()
                max_high = self.sticker_df[symbol]["h"].max()
                min_low = self.sticker_df[symbol]["l"].min()
                max_volume = self.sticker_df[symbol]["v"].max()
                min_volume = self.sticker_df[symbol]["v"].min()
               
                self.trading_day_sticker_stats = {
                    'avg_close': avg_close,
                    'avg_volume': avg_volume,
                    'price_range_perc': (max_high - min_low) / avg_close * 100,
                    'volume_range_ratio': (max_volume - min_volume) / avg_volume
                    }
                
                self.sticker_data['stickers'][symbol]['trading_day_data'] = pd.DataFrame(self.sticker_df[symbol])
                self.sticker_data['stickers'][symbol]['trading_day_sticker_stats'] = pd.DataFrame.from_dict(self.trading_day_sticker_stats)
        else: 
            raise ValueError('recommended_sticker_list is empty or None!')
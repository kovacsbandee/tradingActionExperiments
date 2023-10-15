from typing import List
from .PriceDataGeneratorBase import PriceDataGeneratorBase
import pandas as pd

class AlpacaPriceDataGenerator(PriceDataGeneratorBase):
    
    def initialize_sticker_dict(self):
        self.sticker_data['trading_day'] = self.trading_day.strftime('%Y-%m-%d')
        self.sticker_data['stickers'] = dict()
        if self.recommended_sticker_list is not None:
            for stckr in self.recommended_sticker_list:
                self.sticker_data['stickers'][stckr] = dict()
                self.sticker_data['stickers'][stckr]['trading_day_data'] = None
                self.sticker_data['stickers'][stckr]['trading_day_sticker_stats'] = None
        else:
            raise ValueError("Recommended sticker list is empty.")
                
    def initialize_current_data_window(self):
        if self.recommended_sticker_list is not None:
            for stckr in self.recommended_sticker_list:
                self.current_data_window[stckr] = pd.DataFrame
        else:
            raise ValueError("Recommended sticker list is empty.")
                
    def update_current_data_window(self, minute_bars: List[dict]):
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:               
                self.current_data_window[bar['S']].append(pd.DataFrame(bar))
                if len(self.current_data_window[bar['S']]) > self.data_window_size:
                    self.current_data_window[bar['S']].drop(0)
        else:
            raise ValueError("Minute bar list is empty.")
                            
    def load_watchlist_daily_price_data(self):
        if self.recommended_sticker_list is not None:
            for symbol in self.recommended_sticker_list:

                avg_close = self.current_data_window[symbol]["c"].mean()
                avg_volume = self.current_data_window[symbol]["v"].mean()
                max_high = self.current_data_window[symbol]["h"].max()
                min_low = self.current_data_window[symbol]["l"].min()
                max_volume = self.current_data_window[symbol]["v"].max()
                min_volume = self.current_data_window[symbol]["v"].min()
               
                self.trading_day_sticker_stats = {
                    'avg_close': avg_close,
                    'avg_volume': avg_volume,
                    'price_range_perc': (max_high - min_low) / avg_close * 100,
                    'volume_range_ratio': (max_volume - min_volume) / avg_volume
                    }
                
                self.sticker_data['stickers'][symbol]['trading_day_data'] = pd.DataFrame(self.current_data_window[symbol])
                self.sticker_data['stickers'][symbol]['trading_day_sticker_stats'] = pd.DataFrame.from_dict(self.trading_day_sticker_stats)
        else: 
            raise ValueError('recommended_sticker_list is empty or None!')
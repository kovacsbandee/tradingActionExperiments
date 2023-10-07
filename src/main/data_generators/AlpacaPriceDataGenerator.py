from typing import List
from datetime import datetime, timedelta
from .PriceDataGeneratorBase import PriceDataGeneratorBase
import pandas as pd
import threading
from pandas import DataFrame
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

class AlpacaPriceDataGenerator(PriceDataGeneratorBase):
    
    def initialize_sticker_dict(self):
        self.sticker_dict['trading_day'] = self.trading_day.strftime('%Y-%m-%d')
        self.sticker_dict['stickers'] = dict()
        if self.recommended_sticker_list is not None:
            for stckr in self.recommended_sticker_list:
                self.sticker_dict['stickers'][stckr] = dict()
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
                    
    #NOTE: nem köll
    def load_prev_day_watchlist_data(self):
        if self.recommended_sticker_list:
            for symbol in self.recommended_sticker_list:
                scanning_day = TimeFrame(amount=1, unit=TimeFrameUnit.Minute)
                bars_request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=scanning_day
                )
                
                self.prev_day_data = self.historical_data_client.get_stock_bars(bars_request).df
                self.prev_day_sticker_stats = self._calculate_prev_day_sticker_stats()
        else:
            raise ValueError("Recommended sticker list is empty.")
        
    def _calculate_prev_day_sticker_stats(self) -> dict:
        high = self.prev_day_data['high']
        low = self.prev_day_data['low']
        close = self.prev_day_data['close']
        volume = self.prev_day_data['volume']
        price_range_perc = (high.max() - low.min()) / close.mean() * 100
        volume_range_ratio = (volume.max() - volume.min()) / volume.mean()
        return {
                'avg_close': close.mean(),
                'avg_volume': volume.mean(),
                'price_range_perc': price_range_perc,
                'volume_range_ratio': volume_range_ratio
                }
                            
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
                
                ''' Here is a place, where a-priori constraints like price boundaries could be applied! '''
                
                self.sticker_dict['stickers'][symbol]['trading_day_data'] = trading_day_data
                self.sticker_dict['stickers'][symbol]['trading_day_sticker_stats'] = self.trading_day_sticker_stats
        else: 
            raise ValueError('recommended_sticker_list is empty or None!')
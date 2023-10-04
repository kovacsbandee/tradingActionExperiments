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
                
    def append_to_current_data_window(self, minute_bars: List[dict]):
        #TODO: számolni kell azzal, hogy nem feltétlenül egy listában jönnek az adatok
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:               
                self.current_data_window[bar['S']].append(pd.DataFrame(bar))
                if len(self.current_data_window[bar['S']]) > self.data_window_size:
                    self.current_data_window[bar['S']].drop(0)
        else:
            raise ValueError("Minute bar list is empty.")
                    
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
        # 1) kell egy számláló, ami figyeli, hogy hány websocket-message érkezett, addig nem engedi az algot továbbfutni, 
        #    amíg a counter nem éri el a self.data_window_size-ot
        if self.recommended_sticker_list is not None:
            for ticker in self.recommended_sticker_list['stickers'].keys():
                ticker_symbol = ticker
                
                # ehelyett kell az Alpaca REST hívás
                yahoo_data: DataFrame = yf.download(ticker_symbol,
                            start=self.trading_day - timedelta(1),
                            end=self.trading_day + timedelta(1),
                            interval='1m',
                            progress=False)
                
                # note itt azért még lehet baj!
                yahoo_data.columns = [c.lower() for c in yahoo_data.columns]
                
                trading_day_data = yahoo_data[pd.to_datetime(yahoo_data.index).tz_localize(None) > pd.to_datetime(self.trading_day-timedelta(1))]
                # TODO for Kovi: sticker stats has to be revised and enhanced based on general price plots, comparison between stats and profitability!
                trading_day_sticker_stats = {
                    'avg_close': trading_day_data['close'].mean(),
                    'avg_volume': trading_day_data['volume'].mean(),
                    'price_range_perc': (trading_day_data['high'].max() - trading_day_data['low'].min()) / trading_day_data['close'].mean() * 100,
                    'volume_range_ratio': (trading_day_data['volume'].max() - trading_day_data['volume'].min()) / trading_day_data['volume'].mean()
                    }
                
                prev_day_data = yahoo_data[pd.to_datetime(yahoo_data.index).tz_localize(None) < pd.to_datetime(self.trading_day)]
                prev_sticker_stats = {
                    'avg_close': prev_day_data['close'].mean(),
                    'avg_volume': prev_day_data['volume'].mean(),
                    'price_range_perc': (prev_day_data['high'].max() - prev_day_data['low'].min()) / prev_day_data['close'].mean() * 100,
                    'volume_range_ratio': (prev_day_data['volume'].max() - prev_day_data['volume'].min()) / prev_day_data['volume'].mean()
                    }
                ''' Here is a place, where a-priori constraints like price boundaries could be applied! '''
                
                self.sticker_dict['stickers'][ticker_symbol]['trading_day_data'] = trading_day_data
                self.sticker_dict['stickers'][ticker_symbol]['trading_day_sticker_stats'] = trading_day_sticker_stats
                self.sticker_dict['stickers'][ticker_symbol]['prev_day_data'] = self.prev_day_data
                self.sticker_dict['stickers'][ticker_symbol]['prev_day_stats'] = prev_sticker_stats
        else: 
            raise ValueError('recommended_stickers is None!')
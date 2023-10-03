from typing import List
from datetime import datetime, timedelta
from .PriceDataGeneratorBase import PriceDataGeneratorBase
import pandas as pd
from pandas import DataFrame
from alpaca.data.requests import StockLatestQuoteRequest

class AlpacaPriceDataGenerator(PriceDataGeneratorBase):
    
    def initialize_sticker_dict(self):
        self.sticker_dict['trading_day'] = self.trading_day.strftime('%Y-%m-%d')
        self.sticker_dict['stickers'] = dict()
        if self.recommended_stickers is not None:
            for index, row in self.recommended_stickers.iterrows():
                self.sticker_dict['stickers'][row['sticker']] = dict()
                
    def initialize_current_data_window(self):
        if self.recommended_stickers is not None:
            for index, row in self.recommended_stickers.iterrows():
                self.current_data_window[row['sticker']] = pd.DataFrame
                
    def append_to_current_data_window(self, minute_bars: List[dict]):
        if minute_bars is not None and len(minute_bars) > 0:
            for bar in minute_bars:               
                self.current_data_window[bar['S']].append(pd.DataFrame(bar))
                if len(self.current_data_window[bar['S']]) > self.data_window_size:
                    self.current_data_window[bar['S']].drop(0)
                    
    def load_prev_day_watchlist_data(self):
        """
        Alpaca REST hívás az előző napi stickerekről
        prev_day_data = alpaca.get_barset(...)
                        prev_sticker_stats = {
                    'avg_close': prev_day_data['close'].mean(),
                    'avg_volume': prev_day_data['volume'].mean(),
                    'price_range_perc': (prev_day_data['high'].max() - prev_day_data['low'].min()) / prev_day_data['close'].mean() * 100,
                    'volume_range_ratio': (prev_day_data['volume'].max() - prev_day_data['volume'].min()) / prev_day_data['volume'].mean()
                    }
        """
        request = StockLatestQuoteRequest(symbol_or_symbols=[[sticker for sticker in self.recommended_stickers['sticker']]])
        #TODO: TimeFrame a get_stock_bars-hoz
        latest_multisymbol_quotes = self.historical_data_client.get_stock_bars(request)
                            
    def load_watchlist_daily_price_data(self):
        if self.recommended_stickers is not None:
            for ticker in self.recommended_stickers['stickers'].keys():
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
                self.sticker_dict['stickers'][ticker_symbol]['prev_day_data'] = prev_day_data
                self.sticker_dict['stickers'][ticker_symbol]['prev_day_stats'] = prev_sticker_stats
        else: 
            raise ValueError('recommended_stickers is None!')
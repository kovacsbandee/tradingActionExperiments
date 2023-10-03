from typing import List
import pandas as pd
from pandas import DataFrame
from datetime import timedelta
import yfinance as yf
from joblib import Parallel, delayed
import logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from .PriceDataGeneratorBase import PriceDataGeneratorBase


class PriceDataGenerator(PriceDataGeneratorBase):
    
    """
        Úgy kell átdolgozzuk ezt az osztályt, hogy az előző napi adatok egyszer töltődnek le a watchlist-stickerekhez,
        ezeket eltároljuk egy konstansba, a napi trading data pedig az Alpaca websocketből percenként frissül.
    """

    def load_individual_sticker_data(self) -> List[tuple]:
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
                
                self.recommended_stickers['stickers'][ticker_symbol]['trading_day_data'] = trading_day_data
                self.recommended_stickers['stickers'][ticker_symbol]['trading_day_sticker_stats'] = trading_day_sticker_stats
                self.recommended_stickers['stickers'][ticker_symbol]['prev_day_data'] = prev_day_data
                self.recommended_stickers['stickers'][ticker_symbol]['prev_day_stats'] = prev_sticker_stats
        else: 
            return None 

    def load_watchlist_daily_price_data(self):
        all_sticker_data = self.load_individual_sticker_data()
        return all_sticker_data

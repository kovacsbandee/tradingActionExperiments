import os
from typing import List
from datetime import timedelta
import pandas as pd
from pandas import DataFrame
import yfinance as yf
from joblib import Parallel, delayed

from src_tr.main.enums_and_constants.trading_constants import AVG_OPEN, STD_OPEN, SYMBOL, PRICE_RANGE_PERC, AVG_VOLUME, VOLUME_RANGE_RATIO, SCANNING_DAY
from src_tr.main.scanners.ScannerBase import ScannerBase

class PreMarketDumbScanner(ScannerBase):

    def __init__(self, 
                 trading_day, 
                 scanning_day, 
                 stickers,
                 lower_price_boundary=10, 
                 upper_price_boundary=250, 
                 price_range_perc_cond=10, 
                 avg_volume_cond=25000):
        super().__init__(trading_day, scanning_day, stickers)
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.price_range_perc_cond = price_range_perc_cond
        self.avg_volume_cond = avg_volume_cond

    def _download_sticker_history(self, sticker: str):
        start_date = self.scanning_day
        end_date = self.trading_day
        try:
            sticker: yf.Ticker = yf.Ticker(sticker)
            return sticker.history(start=start_date, end=end_date, interval='1m', period='1d') if sticker else None
        except Exception as e:
            print(str(e))
            return None

    def get_pre_market_stats(self, sticker: str) -> dict:
        '''
        Downloads the sticker price data and calculates the scanner statistics and returns a dictionary with them.
        '''
        try:
            sticker_history = self._download_sticker_history(sticker=sticker)

            if sticker_history is not None and not sticker_history.empty:

                # TODO: itt ki kell találni milyen egyéb statisztikákat akarunk még nézni.
                avg_open = sticker_history['Open'].mean()
                median_open = sticker_history['Open'].median()
                std_open = sticker_history['Open'].std()

                avg_close = sticker_history['Close'].mean()
                median_close = sticker_history['Close'].median()

                high_max = sticker_history['High'].max()
                low_min = sticker_history['Low'].min()

                avg_volume = sticker_history['Volume'].mean()
                median_volume = sticker_history['Volume'].median()
                volume_max = sticker_history['Volume'].max()
                volume_min = sticker_history['Volume'].min()

                price_range_perc = 0
                volume_range_ratio = 0
                close_monetary_avg_volume = 0
                close_monetary_min_volume = (sticker_history['Close'] * sticker_history['Volume']).min()

                if not pd.isnull(avg_volume) and avg_volume != 0:
                    price_range_perc = (high_max - low_min) / ((high_max + low_min) / 2) * 100
                    volume_range_ratio = (volume_max - volume_min) / avg_volume
                    close_monetary_avg_volume = median_close * median_volume

                # itt mindig minden statisztikát vissza kell adni, amit kiszámolunk!
                return {
                    SYMBOL: sticker,
                    AVG_OPEN: avg_open,
                    'median_open': median_open,
                    STD_OPEN: std_open,
                    'avg_close': avg_close,
                    'median_close': median_close,
                    'high_max': high_max,
                    'low_min': low_min,
                    AVG_VOLUME: avg_volume,
                    'median_volume': median_volume,
                    'max_volume': volume_max,
                    'min_volume': volume_min,
                    'close_monetary_avg_volume': close_monetary_avg_volume,
                    'close_monetary_min_volume': close_monetary_min_volume,
                    PRICE_RANGE_PERC: price_range_perc,
                    VOLUME_RANGE_RATIO: volume_range_ratio
                }
            else:
                return None
        except Exception as e:
            print(str(e))
            return None

    def calculate_filtering_stats(self) -> List:
        self.pre_market_stats = self._create_pre_market_stats()
        proj_path = os.environ['PROJECT_PATH']
        date = self.trading_day.strftime('%Y_%m_%d')
        self.pre_market_stats.to_csv(f'{proj_path}_database/scanner_stats/pre_market_stats_{date}.csv', index=False)
        return self.pre_market_stats

    def _create_pre_market_stats(self) -> DataFrame:
        pre_market_sticker_stats = \
            Parallel(n_jobs=-1)(delayed(self.get_pre_market_stats)(sticker) for sticker in self.stickers)
                 
        pre_market_sticker_stats = [stats for stats in pre_market_sticker_stats if stats is not None]
        
        try:
            return pd.DataFrame.from_records(pre_market_sticker_stats)
        except Exception as e:
            print(f'Failed to create pre_market_stats DataFrame: {str(e)}')
            return None
        
    def recommend_premarket_watchlist(self) -> List[dict]:
        #self.recommended_stickers: pd.DataFrame = self.pre_market_stats[
        #    (self.lower_price_boundary < self.pre_market_stats[AVG_OPEN]) & \
        #    (self.pre_market_stats[AVG_OPEN] < self.upper_price_boundary) & \
        #    (self.price_range_perc_cond < self.pre_market_stats[PRICE_RANGE_PERC]) & \
        #    (self.avg_volume_cond < self.pre_market_stats[AVG_VOLUME])]

        self.recommended_stickers: pd.DataFrame = self.pre_market_stats
        print(f'The recommended watchlist for {self.trading_day} is the following DataFrame: {self.recommended_stickers}')
        sticker_dict_list = []
        if self.recommended_stickers is not None:
            for index, row in self.recommended_stickers.iterrows():
                st_dict = {
                    SYMBOL : row[SYMBOL],
                    AVG_OPEN : row[AVG_OPEN],
                    STD_OPEN : row[STD_OPEN]
                }
                # Itt azt gondolom, hogy érdemes lenne beletenni minden statisztikát, amit számolunk,
                # így lenne lehetőség arra, hogy vizsgáljuk az összefüggéseket a premarket scanner statisztikái és a kereskedés eredményei között
                sticker_dict_list.append(st_dict)
                #sticker_dict_list.append(row['sticker'])
        
        return sticker_dict_list




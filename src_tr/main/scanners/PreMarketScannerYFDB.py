# az ebben a file-ban javasolt változtatásokat mindegyik scanner-ben meg kell csinálni,
# esetleg már az ősosztályba be lehetne dolgozni

import os
from typing import List
from datetime import timedelta
import pandas as pd
import numpy as np
from pandas import DataFrame
import yfinance as yf
from joblib import Parallel, delayed

from src_tr.main.scanners.ScannerBase import ScannerBase
import config


class PreMarketScannerYFDB(ScannerBase):

    def __init__(self,
                 trading_day,
                 scanning_day,
                 symbols,
                 lower_price_boundary=10,
                 upper_price_boundary=250,
                 price_range_perc_cond=10,
                 avg_volume_cond=25000):  # TODO: ez csak bele van kókányolva, mert függ a tőkétől és a részvény ártól is! újra kell gondolni
        super().__init__(trading_day, scanning_day, symbols)
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.price_range_perc_cond = price_range_perc_cond
        self.avg_volume_cond = avg_volume_cond

    def _download_symbol_history(self, symbol: str):
        '''
        Downloads the scanning day minutely price data from yahoo finance,
        if yfinance returns an error it raises an exception.
        '''
        try:
            scanning_day_str = self.scanning_day.strftime('%Y_%m_%d')
            symbol_scanning_day_df = pd.read_csv(
                f'{config.db_path}/daywise_database/stock_prices_for_{scanning_day_str}/csvs/{symbol}.csv')
            symbol_scanning_day_df.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'adj close', 'Volume']
            return symbol_scanning_day_df
        except Exception as e:
            print(str(e))
            return None

    def get_pre_market_stats(self, symbol: str) -> dict:
        '''
        Downloads the symbol price data and calculates the scanner statistics and returns a dictionary with them.
        '''
        try:
            symbol_history = self._download_symbol_history(symbol=symbol)

            if symbol_history is not None and not symbol_history.empty:

                # TODO: itt ki kell találni milyen egyéb statisztikákat akarunk még nézni.
                avg_open = symbol_history['Open'].mean()
                median_open = symbol_history['Open'].median()
                std_open = symbol_history['Open'].std()

                avg_close = symbol_history['Close'].mean()
                median_close = symbol_history['Close'].median()

                high_max = symbol_history['High'].max()
                low_min = symbol_history['Low'].min()
                minute_oc_price_diff = symbol_history['Open'] - symbol_history['Close']
                minute_oc_price_diff_avg = np.mean(minute_oc_price_diff)
                minute_oc_price_diff_median = np.median(minute_oc_price_diff)
                minute_oc_price_diff_std = np.std(minute_oc_price_diff)

                avg_volume = symbol_history['Volume'].mean()
                median_volume = symbol_history['Volume'].median()
                volume_max = symbol_history['Volume'].max()
                volume_min = symbol_history['Volume'].min()

                price_range_perc = 0
                volume_range_ratio = 0
                close_monetary_avg_volume = 0
                close_monetary_min_volume = (symbol_history['Close'] * symbol_history['Volume']).min()

                if not pd.isnull(avg_volume) and avg_volume != 0:
                    price_range_perc = (high_max - low_min) / ((high_max + low_min) / 2) * 100
                    volume_range_ratio = (volume_max - volume_min) / avg_volume
                    close_monetary_avg_volume = median_close * median_volume

                # itt mindig minden statisztikát vissza kell adni, amit kiszámolunk!
                return {
                    'symbol': symbol,
                    'avg_open': avg_open,
                    'median_open': median_open,
                    'std_open': std_open,
                    'avg_close': avg_close,
                    'median_close': median_close,
                    'high_max': high_max,
                    'low_min': low_min,
                    'minute_oc_price_diff_avg': minute_oc_price_diff_avg,
                    'minute_oc_price_diff_median': minute_oc_price_diff_median,
                    'minute_oc_price_diff_std': minute_oc_price_diff_std,
                    'avg_volume': avg_volume,
                    'median_volume': median_volume,
                    'max_volume': volume_max,
                    'min_volume': volume_min,
                    'close_monetary_avg_volume': close_monetary_avg_volume,
                    'close_monetary_min_volume': close_monetary_min_volume,
                    'price_range_perc': price_range_perc,
                    'volume_range_ratio': volume_range_ratio
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
        # TODO: a path itt is kívülről jöjjön configból/.env-ből, hogy ne kelljen mindig átírni
        self.pre_market_stats.to_csv(f'{proj_path}_database/scanner_stats/pre_market_stats_{date}.csv', index=False)
        return self.pre_market_stats

    def _create_pre_market_stats(self) -> DataFrame:
        pre_market_symbol_stats = \
            Parallel(n_jobs=-1)(delayed(self.get_pre_market_stats)(symbol) for symbol in self.symbols)

        pre_market_symbol_stats = [stats for stats in pre_market_symbol_stats if stats is not None]

        try:
            return pd.DataFrame.from_records(pre_market_symbol_stats)
        except Exception as e:
            print(f'Failed to create pre_market_stats DataFrame: {str(e)}')
            return None

    def recommend_premarket_watchlist(self) -> List[dict]:
        '''
        Filters the pre_market_stats dataframe with, price boundaries and price ranges and volume.
        '''
        self.recommended_symbols: pd.DataFrame = self.pre_market_stats[
            (self.lower_price_boundary < self.pre_market_stats['avg_open']) & \
            (self.pre_market_stats['avg_open'] < self.upper_price_boundary) & \
            (self.price_range_perc_cond < self.pre_market_stats['price_range_perc']) & \
            (self.avg_volume_cond < self.pre_market_stats['avg_volume'])]
        print(
            f'The recommended watchlist for {self.trading_day} is the following DataFrame: {self.recommended_symbols}')

        symbol_dict_list = []
        if self.recommended_symbols is not None:
            for index, row in self.recommended_symbols.iterrows():
                st_dict = {
                    'symbol': row['symbol'],
                    'avg_open': row['avg_open'],
                    'std_open': row['std_open']
                }
                symbol_dict_list.append(st_dict)
                # symbol_dict_list.append(row['symbol'])
        return symbol_dict_list




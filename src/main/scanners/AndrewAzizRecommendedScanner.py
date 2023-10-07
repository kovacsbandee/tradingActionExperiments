import os
from typing import List
from datetime import timedelta
import pandas as pd
from pandas import DataFrame
import yfinance as yf
from joblib import Parallel, delayed
from plots.plots import create_histograms

from .ScannerBase import ScannerBase

class AndrewAzizRecommendedScanner(ScannerBase):

    def __init__(self, lower_price_boundary, upper_price_boundary, price_range_perc_cond, avg_volume_cond):
        super.__init__()
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.price_range_perc_cond = price_range_perc_cond
        self.avg_volume_cond = avg_volume_cond
    
    def get_pre_market_stats(self, sticker: str) -> dict:
        start_date = self.scanning_day
        end_date = self.trading_day
        
        #NOTE: nem muszáj ezzel a megoldással letölteni, csak így jobban tudtam debugolni
        try:
            ticker = yf.Ticker(sticker)
            ticker_history = ticker.history(start=start_date, end=end_date, interval='1h', period='1d') if ticker else None
            
            if ticker_history is not None and not ticker_history.empty:
                #TODO: kell még az 
                # index (DateTimeIndex)
                # adatok a megelőző ÉS a trading napról
                # itt csak a megelőző napot számoljuk, így kell a tz_localize(None) és szűrés
                
                avg_close = ticker_history['Close'].mean()
                high_max = ticker_history['High'].max()
                low_min = ticker_history['Low'].min()
                avg_volume = ticker_history['Volume'].mean()
                volume_max = ticker_history['Volume'].max()
                volume_min = ticker_history['Volume'].min()
                price_range_perc = 0
                volume_range_ratio = 0
                
                if not pd.isnull(avg_volume) and avg_volume != 0: 
                    price_range_perc = (high_max - low_min) / avg_close * 100
                    volume_range_ratio = (volume_max - volume_min) / avg_volume
                    
                return {
                    'sticker': sticker, # TODO: ref -> generate_price_data -> továbbadhatnánk az oda kellő adatokat is
                    'avg_close': avg_close,
                    'avg_volume': avg_volume,
                    'price_range_perc': price_range_perc,
                    'volume_range_ratio': volume_range_ratio
                    }
            else:
                return None
        except Exception as e:
            print(f"No data available for sticker: {sticker}")
            return None

    def calculate_filtering_stats(self, save_csv: bool = False) -> List:
        self.pre_market_stats = self._create_pre_market_stats()
        save_date = self.scanning_day.strftime('%Y-%m-%d')
        if save_csv:
            self.save_stats_to_csv(save_date) 

        if self.pre_market_stats is not None:
            create_histograms(plot_df=self.pre_market_stats[[c for c in self.pre_market_stats.columns if c != 'sticker']],
                            plot_name=f'pre_market_stats_hist_{save_date}')
            print('Pre market statistics histograms can be found in the plots/plot_store directory, '
                'please check for avg_volume, price_range_perc as further constraints')
        return self.pre_market_stats
        
    def _create_pre_market_stats(self) -> DataFrame:
        pre_market_sticker_stats = \
            Parallel(n_jobs=16)(delayed(self.get_pre_market_stats)(sticker) for sticker in self.stickers)
                 
        pre_market_sticker_stats = [stats for stats in pre_market_sticker_stats if stats is not None]
        
        try:   
            return pd.DataFrame.from_records(pre_market_sticker_stats)
        except Exception as e:
            print(f'Failed to create pre_market_stats DataFrame: {str(e)}') #Exception string helyett valami beszédesebb legyen
            return None
    
    def save_stats_to_csv(self, save_date):
        data_path = f'{self.project_path}/data_store'
        files_to_remove = [f for f in data_path if f'pre_market_stats_{save_date}' in f]
        if len(os.listdir(data_path)):
            for f in files_to_remove:
                os.remove(os.listdir(f'{data_path}/{f}'))
        self.pre_market_stats.to_csv(path_or_buf=f'{self.project_path}/data_store/pre_market_stats_{save_date}', index=False)
        
    def recommend_premarket_watchlist(self) -> List[str]:
        self.recommended_stickers = self.pre_market_stats[
            (self.lower_price_boundary < self.pre_market_stats['avg_close']) & \
            (self.pre_market_stats['avg_close'] < self.upper_price_boundary) & \
            (self.price_range_perc_cond < self.pre_market_stats['price_range_perc']) & \
            (self.avg_volume_cond < self.pre_market_stats['avg_volume'])]
        print(f'The recommended watchlist for {self.trading_day} is the following DataFrame: {self.recommended_stickers}')
        sticker_string_list = [] # TODO: ez így kókányolás, ki kell találni valami jobbat, illetve kérdés, hogy a Scannerből kell-e az összes adat, 
        if self.recommended_stickers is not None:
            for index, row in self.recommended_stickers.iterrows():
                sticker_string_list.append(row['sticker'])
        
        return sticker_string_list




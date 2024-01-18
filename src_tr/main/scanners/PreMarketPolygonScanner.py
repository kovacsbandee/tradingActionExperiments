import os
from typing import List
from datetime import datetime
import pandas as pd
from pandas import DataFrame
import yfinance as yf
from polygon import RESTClient
from joblib import Parallel, delayed

from src_tr.main.enums_and_constants.trading_constants import AVG_OPEN, STD_OPEN, SYMBOL, PRICE_RANGE_PERC, AVG_VOLUME, VOLUME_RANGE_RATIO
from src_tr.main.scanners.ScannerBase import ScannerBase

class PreMarketPolygonScanner(ScannerBase):

    def __init__(self, 
                 trading_day, 
                 scanning_day, 
                 stickers,
                 lower_price_boundary=10, 
                 upper_price_boundary=250, 
                 price_range_perc_cond=10, 
                 avg_volume_cond=25000): # TODO: ez csak bele van kókányolva, mert függ a tőkétől és a részvény ártól is! újra kell gondolni
        super().__init__(trading_day, scanning_day, stickers)
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.price_range_perc_cond = price_range_perc_cond
        self.avg_volume_cond = avg_volume_cond

    # Ha jól értem ezt kellene megoldani az aiohttp-vel, akkor aszinkron tudnánk küldeni az API hívásokat, itt a Paralelle nem használ.
    # Illetve akkor azt is tudni kell majd, hogy hány API hívást tudunk csinálni egy nap!
    # Ezek mellett az is fontos kérdés, hogy hogyan tudjuk ellenőrizni, hogy melyik tőzsdéről jön az adat?
    def _download_sticker_history(self, ticker: str):
        start_date = self.scanning_day
        end_date = self.trading_day
        aggs = []
        client = RESTClient(api_key="Rdcy29x7wooeMAlqKIsnTfDiHOaz0J_d")
        aggregate_list = client.list_aggs(ticker=ticker, multiplier=1, timespan="minute", from_=start_date, to=end_date, limit=50000)
        try:
            for a in aggregate_list:
                a_dict = a.__dict__
                ts = int(a.timestamp)
                ts /= 1000
                convert_ts = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                a_dict['timestamp'] = convert_ts
                a_dict['symbol'] = ticker
                aggs.append(a_dict)
        except Exception as ex:
            print(f'Error: {ex}')
            
        if len(aggs) > 0:
            bar_dict_list = []
            for i in aggs:
                bar_dict_list.append(i)
                
            if bar_dict_list:
                bar_df = pd.DataFrame(bar_dict_list)
                bar_df.set_index('timestamp', inplace=True)
            
            return bar_df
    
    def get_pre_market_stats(self, sticker: str) -> dict:
        try:
            sticker_history = self._download_sticker_history(ticker=sticker)
            
            if sticker_history is not None and not sticker_history.empty:
                
                avg_close = sticker_history['close'].mean() # TODO: nem kell?
                avg_open = sticker_history['open'].mean()
                std_open = sticker_history['open'].std()
                high_max = sticker_history['high'].max()
                low_min = sticker_history['low'].min()
                avg_volume = sticker_history['volume'].mean()
                volume_max = sticker_history['volume'].max()
                volume_min = sticker_history['volume'].min()
                price_range_perc = 0
                volume_range_ratio = 0
                
                if not pd.isnull(avg_volume) and avg_volume != 0: 
                    price_range_perc = (high_max - low_min) / ((high_max + low_min) / 2) * 100
                    volume_range_ratio = (volume_max - volume_min) / avg_volume
                    
                return {
                    SYMBOL: sticker,
                    'avg_close': avg_close, # TODO: nem kell?
                    AVG_OPEN : avg_open,
                    STD_OPEN : std_open,
                    AVG_VOLUME: avg_volume,
                    PRICE_RANGE_PERC: price_range_perc,
                    VOLUME_RANGE_RATIO: volume_range_ratio
                    }
            else:
                return None
        except Exception as e:
            print(str(e))
            return None

    # Itt miért kell a calculate_filtering_stats és a _create_pre_market_stats is?
    def calculate_filtering_stats(self) -> List:
        self.pre_market_stats = self._create_pre_market_stats()
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
        self.recommended_stickers: pd.DataFrame = self.pre_market_stats[
            (self.lower_price_boundary < self.pre_market_stats[AVG_OPEN]) & \
            (self.pre_market_stats[AVG_OPEN] < self.upper_price_boundary) & \
            (self.price_range_perc_cond < self.pre_market_stats[PRICE_RANGE_PERC]) & \
            (self.avg_volume_cond < self.pre_market_stats[AVG_VOLUME])]
        print(f'The recommended watchlist for {self.trading_day} is the following DataFrame: {self.recommended_stickers}')
        sticker_dict_list = []
        if self.recommended_stickers is not None:
            # általában nem jó ötlet pandas dataframe-en iterálni, van benne egy csomó okos vektor művelet, ami sokkal gyorsabb pl.:
            # sticker_dict_list.append(recommended_stickers.to_dict('records')
            for index, row in self.recommended_stickers.iterrows():
                st_dict = {
                    SYMBOL : row[SYMBOL],
                    AVG_OPEN : row[AVG_OPEN],
                    STD_OPEN : row[STD_OPEN]
                }
                sticker_dict_list.append(st_dict)
                #sticker_dict_list.append(row['sticker'])
        
        return sticker_dict_list




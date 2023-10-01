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

    # TODO: hülyeség az egész scannerből átadás, hiszen itt mindig az adott napra vonatkozó, sőt
    # streamből jövő trading data-t fogjuk percenként töltögetni
    def load_individual_sticker_data(self) -> List[tuple]:
        all_sticker_data = []
        
        if self.sticker_data is not None:
            # note itt azért még lehet baj!
            
            for index, row in self.sticker_data.iterrows():
                sticker = row['sticker']# TODO: csekkold!
                yahoo_data: DataFrame = yf.download(sticker,
                            start=self.trading_day - timedelta(1),
                            end=self.trading_day + timedelta(1),
                            interval='1m',
                            progress=False)
                # TODO: ez így most üres, tehát valóban csak a megelőző napi adatok jönnek be, ezt aktualizálni kell a scannerben is
                yahoo_data.columns = [c.lower() for c in yahoo_data.columns]
                trading_day_data = yahoo_data[pd.to_datetime(yahoo_data.index).tz_localize(None) > pd.to_datetime(self.trading_day-timedelta(1))]
                # TODO for Kovi: sticker stats has to be revised and enhanced based on general price plots, comparison between stats and profitability!
                trading_day_sticker_stats = \
                    {'avg_close': trading_day_data['close'].mean(),
                    'avg_volume': trading_day_data['volume'].mean(),
                    'price_range_perc': (trading_day_data['high'].max() - trading_day_data['low'].min()) / trading_day_data['close'].mean() * 100,
                    'volume_range_ratio': (trading_day_data['volume'].max() - trading_day_data['volume'].min()) / trading_day_data['volume'].mean()}
                prev_day_data = yahoo_data[pd.to_datetime(yahoo_data.index).tz_localize(None) < pd.to_datetime(self.trading_day)]
                prev_sticker_stats = \
                    {'avg_close': prev_day_data['close'].mean(),
                    'avg_volume': prev_day_data['volume'].mean(),
                    'price_range_perc': (prev_day_data['high'].max() - prev_day_data['low'].min()) / prev_day_data['close'].mean() * 100,
                    'volume_range_ratio': (prev_day_data['volume'].max() - prev_day_data['volume'].min()) / prev_day_data['volume'].mean()}
                ''' Here is a place, where a-priori constraints like price boundaries could be applied! '''
                all_sticker_data.append((sticker, trading_day_data, trading_day_sticker_stats, prev_day_data, prev_sticker_stats))
        else: 
            return None 

    def load_watchlist_daily_price_data(self):
        all_sticker_data = self.load_individual_sticker_data()
        # NOTE: ez itten nagyon zagyva nekem egyelőre, valahogy egyszerűsíteni köllene
        if all_sticker_data:
            for i, sticker in enumerate(all_sticker_data):
                if sticker is not None:
                    self.exp_dict['stickers'][sticker[0]]['trading_day_data'] = sticker[1]
                    self.exp_dict['stickers'][sticker[0]]['trading_day_sticker_stats'] = sticker[2]
                    self.exp_dict['stickers'][sticker[0]]['prev_day_data'] = sticker[3]
                    self.exp_dict['stickers'][sticker[0]]['prev_day_stats'] = sticker[4]

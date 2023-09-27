import pandas as pd
from datetime import timedelta
import yfinance as yf
from joblib import Parallel, delayed
import logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

from .PriceDataGeneratorBase import PriceDataGeneratorBase


class PriceDataGenerator(PriceDataGeneratorBase):

    # TODO: végig kell iterálni a sticker_data DataFrame-en
    def load_individual_sticker_data(self):
        if self.sticker_data is not None:
            sticker = self.sticker_data['sticker']# TODO: csekkold!
            # note itt azért még lehet baj!
            self.sticker_data.columns = [c.lower() for c in self.sticker_data.columns]
            # TODO: ez így most üres, tehát valóban csak a megelőző napi adatok jönnek be, ezt aktualizálni kell a scannerben is
            trading_day_data = self.sticker_data[pd.to_datetime(self.sticker_data.index).tz_localize(None) > pd.to_datetime(self.trading_day-timedelta(1))]
            # TODO for Kovi: sticker stats has to be revised and enhanced based on general price plots, comparison between stats and profitability!
            trading_day_sticker_stats = \
                {
                    'avg_close': trading_day_data['avg_close'],
                    'avg_volume': trading_day_data['avg_volume'],
                    'price_range_perc': trading_day_data['price_range_perc'],
                    'volume_range_ratio': trading_day_data['volume_range_ratio']
                 }
            prev_day_data = self.sticker_data[pd.to_datetime(self.sticker_data.index).tz_localize(None) < pd.to_datetime(self.trading_day)]
            prev_sticker_stats = \
                {
                    'avg_close': prev_day_data['avg_close'],
                    'avg_volume': prev_day_data['avg_volume'],
                    'price_range_perc': prev_day_data['price_range_perc'],
                    'volume_range_ratio': prev_day_data['volume_range_ratio']
                 }
            ''' Here is a place, where a-priori constraints like price boundaries could be applied! '''
            return (sticker, trading_day_data, trading_day_sticker_stats, prev_day_data, prev_sticker_stats)
        else: 
            return None

    def load_watchlist_daily_price_data(self):
        all_sticker_data = self.load_individual_sticker_data()
        # NOTE: ez itten nagyon zagyva nekem egyelőre, valahogy egyszerűsíteni köllene
        for i, sticker in enumerate(all_sticker_data): # TODO: itt is DF-en iterálunk végig, nem lesz jó az enumerate
            if sticker is not None:
                self.exp_dict['stickers'][sticker[0]]['trading_day_data'] = sticker[1]
                self.exp_dict['stickers'][sticker[0]]['trading_day_sticker_stats'] = sticker[2]
                self.exp_dict['stickers'][sticker[0]]['prev_day_data'] = sticker[3]
                self.exp_dict['stickers'][sticker[0]]['prev_day_stats'] = sticker[4]

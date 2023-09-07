import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from joblib import Parallel, delayed


class generatePriceData:

    def __init__(self, date, exp_dict, lower_price_boundary=10, upper_price_boundary=100):
        self.date = date
        self.date = datetime.strptime(date, '%Y-%m-%d')
        self.exp_dict = exp_dict
        self.lower_price_boundary=lower_price_boundary
        self.upper_price_boundary = upper_price_boundary

    def load_individual_sticker_data(self, sticker):
        try:
            sticker_data = yf.download(sticker, start=self.date,
                                                end=self.date + timedelta(1),
                                                interval='1m')
        except:
            pass
        if sticker_data is not None:
            if self.lower_price_boundary < sticker_data['Close'].mean() and sticker_data['Close'].mean() < self.upper_price_boundary:
                sticker_data.columns = [c.lower() for c in sticker_data.columns]
                # TODO: sticker stats has to be revised and enhanced based on general price plots
                sticker_stats = \
                    {'avg_close': sticker_data['close'].mean(),
                     'avg_volume': sticker_data['volume'].mean(),
                     'price_range_perc': (sticker_data['high'].max() - sticker_data['low'].min()) / sticker_data['close'].mean() * 100,
                     'volume_range_ratio': (sticker_data['volume'].max() - sticker_data['volume'].min()) / sticker_data['volume'].mean()}
                return (sticker, sticker_data, sticker_stats)


    def load_watchlist_daily_price_data(self):
        stickers = [s for s in self.exp_dict['stickers'].keys()]
        data = Parallel(n_jobs=16)(delayed(self.load_individual_sticker_data)(sticker) for sticker in stickers)
        for sticker in data:
            if sticker is not None:
                self.exp_dict['stickers'][sticker[0]]['data'] = sticker[1]
                self.exp_dict['stickers'][sticker[0]]['stats'] = sticker[2]




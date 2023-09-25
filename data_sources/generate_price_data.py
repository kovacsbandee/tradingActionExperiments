import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from joblib import Parallel, delayed
import logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

"""
    Ha többféle priceData generálásra is lehet szükség, akkor itt is lehet öröklést alkalmazni.
    Ha csak egy kalkulációs modul, akkor lehet, hogy nem kell osztályba szervezni.
"""

class generatePriceData:

    # TODO: a date (lehetne trading_day) benne van az exp_dict arg-ban elvileg
    def __init__(self, date, exp_dict, lower_price_boundary=10, upper_price_boundary=100, lower_volume_boundary=10000):
        self.date = date
        self.date = datetime.strptime(date, '%Y-%m-%d')
        self.exp_dict = exp_dict

    def load_individual_sticker_data(self, sticker): # TODO: a sticker mindig string?
        # TODO: kérdés, hogy itt miért töltsük le újra a sticker adatokat, ha már a Scannerben is lekérdeztük
        # a sticker-stringek helyett tovább lehetne adni a szükséges értékekkel töltött dict-et a scannerből
        # a scannerben lévő számolás lehetne külön modul, ami megkapja a paramétereket, ezek közül adhatnánk tovább ide, ami kell
        try:
            sticker_data = yf.download(sticker,
                                       start=self.date - timedelta(days=1),
                                       end=self.date + timedelta(days=1),
                                       interval='1m',
                                       progress=False)
            # note itt azért még lehet baj!
            sticker_data.columns = [c.lower() for c in sticker_data.columns]
            trading_day_data = sticker_data[pd.to_datetime(sticker_data.index).tz_localize(None) > pd.to_datetime(self.date-timedelta(1))]
            # TODO for Kovi: sticker stats has to be revised and enhanced based on general price plots, comparison between stats and profitability!
            trading_day_sticker_stats = \
                {'avg_close': trading_day_data['close'].mean(),
                 'avg_volume': trading_day_data['volume'].mean(),
                 'price_range_perc': (trading_day_data['high'].max() - trading_day_data['low'].min()) / trading_day_data['close'].mean() * 100,
                 'volume_range_ratio': (trading_day_data['volume'].max() - trading_day_data['volume'].min()) / trading_day_data['volume'].mean()}
            prev_day_data = sticker_data[pd.to_datetime(sticker_data.index).tz_localize(None) < pd.to_datetime(self.date)]
            prev_sticker_stats = \
                {'avg_close': prev_day_data['close'].mean(),
                 'avg_volume': prev_day_data['volume'].mean(),
                 'price_range_perc': (prev_day_data['high'].max() - prev_day_data['low'].min()) / prev_day_data['close'].mean() * 100,
                 'volume_range_ratio': (prev_day_data['volume'].max() - prev_day_data['volume'].min()) / prev_day_data['volume'].mean()}
            ''' Here is a place, where a-priori constraints like price boundaries could be applied! '''
            return (sticker, trading_day_data, trading_day_sticker_stats, prev_day_data, prev_sticker_stats)
        except:
            # TODO: biztos, hogy nem jobb, ha None megy vissza és csekkolunk?
            blank_sticker_stats = \
                {'avg_close': 0.0,
                 'avg_volume': 0.0,
                 'price_range_perc': 0.0,
                 'volume_range_ratio': 0.0}
            blank_df = pd.DataFrame(columns=['date', 'high', 'low', 'close', 'volume'])
            return (sticker, blank_df, blank_sticker_stats, blank_df, blank_sticker_stats)


    def load_watchlist_daily_price_data(self):
        #TODO: ha itt majd újra listává alakítjuk, akkor miért kellett első körben dict?
        stickers = [s for s in self.exp_dict['stickers'].keys()]
        all_sticker_data = Parallel(n_jobs=16)(delayed(self.load_individual_sticker_data)(sticker) for sticker in stickers)
        # TODO: kell itt az enumerate? az indexet nem használjuk
        # NOTE: ez itten nagyon zagyva nekem egyelőre, valahogy egyszerűsíteni köllene
        for i, sticker in enumerate(all_sticker_data):
            if sticker is not None:
                self.exp_dict['stickers'][sticker[0]]['trading_day_data'] = sticker[1]
                self.exp_dict['stickers'][sticker[0]]['trading_day_sticker_stats'] = sticker[2]
                self.exp_dict['stickers'][sticker[0]]['prev_day_data'] = sticker[3]
                self.exp_dict['stickers'][sticker[0]]['prev_day_stats'] = sticker[4]

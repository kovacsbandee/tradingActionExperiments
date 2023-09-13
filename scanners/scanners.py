from datetime import datetime, timedelta
import os
import pandas as pd
import yfinance as yf
from joblib import Parallel, delayed
from plots.plots import create_histograms

def get_nasdaq_stickers(path: str='F:/tradingActionExperiments'):
    daily_nasdaq_stickers = pd.read_csv(f'{path}/data_store/daily_nasdaq_stickers.csv')
    daily_nasdaq_stickers['Last Sale'] = daily_nasdaq_stickers['Last Sale'].str.lstrip('$').astype(float)
    daily_nasdaq_stickers = daily_nasdaq_stickers[(~daily_nasdaq_stickers['Market Cap'].isna()) & \
                                                  (daily_nasdaq_stickers['Market Cap'] != 0.0)]
    return list(daily_nasdaq_stickers['Symbol'].unique())


class andrewAzizRecommendedScanner:

    def __init__(self, trading_day: datetime, stickers: list = None):
        self.trading_day = datetime.strptime(trading_day, '%Y-%m-%d')
        if self.trading_day.strftime('%A') == 'Sunday' or self.trading_day.strftime('%A') == 'Saturday':
            raise ValueError(f'{self.trading_day} is not a valid trading day, because it is on a weekend. Choose a weekday!')
        if (self.trading_day - timedelta(1)).strftime('%A') == 'Sunday':
            self.scanning_day = self.trading_day - timedelta(2)
        else:
            self.scanning_day = self.trading_day - timedelta(1)
        self.stickers = get_nasdaq_stickers() if stickers is None else stickers
        self.pre_market_stats = None
        self.recommended_stickers = []
        self.name = 'andrewAzizRecommendedScanner'

    def get_pre_market_stats(self, sticker: str):
        sticker_data = None
        try:
            sticker_data = yf.download(sticker,
                                       start=self.scanning_day,
                                       end=self.scanning_day + timedelta(1),
                                       interval='1m',
                                       progress=False,
                                       show_errors=False)
        except:
            pass
        if sticker_data is not None:
            return {'sticker': sticker,
                    'avg_close': sticker_data['Close'].mean(),
                    'avg_volume': sticker_data['Volume'].mean(),
                    'price_range_perc': (sticker_data['High'].max() - sticker_data['Low'].min()) / sticker_data['Close'].mean() * 100,
                    'volume_range_ratio': (sticker_data['Volume'].max() - sticker_data['Volume'].min()) / sticker_data['Volume'].mean()}
        else:
            return {'sticker': sticker,
                    'avg_close': 0,
                    'avg_volume': 0,
                    'price_range_perc': 0,
                    'volume_range_ratio':0}


    def get_filtering_stats(self, save_csv: bool = False, proj_path='F:/tradingActionExperiments'):
        pre_market_sticker_stats = \
            Parallel(n_jobs=16)(delayed(self.get_pre_market_stats)(sticker) for sticker in self.stickers)

        self.pre_market_stats = pd.DataFrame.from_records(pre_market_sticker_stats)
        save_date = self.scanning_day.strftime('%Y-%m-%d')
        if save_csv:
            data_path = f'{proj_path}/data_store'
            files_to_remove = [f for f in data_path if f'pre_market_stats_{save_date}' in f]
            if len(os.listdir(data_path)):
                for f in files_to_remove:
                    os.remove(os.listdir(f'{data_path}/{f}'))
            else:
                pass
            self.pre_market_stats.to_csv(path_or_buf=f'{proj_path}/data_store/pre_market_stats_{save_date}', index=False)
        create_histograms(plot_df=self.pre_market_stats[[c for c in self.pre_market_stats.columns if c != 'sticker']],
                          plot_name=f'pre_market_stats_hist_{save_date}')
        print('Pre market statistics histograms can be found in the plots/plot_store directory, '
              'please check for avg_volume, price_range_perc as further constraints')

    def recommend_premarket_watchlist(self, price_range_perc_cond: int = 10, avg_volume_cond: int = 25000):
        # TODO a filter here could be applied based on the other statistics: e.g. prica range between 10 and 100$
        self.recommended_stickers = self.pre_market_stats[(price_range_perc_cond < self.pre_market_stats['price_range_perc']) & \
                                                          (avg_volume_cond < self.pre_market_stats['avg_volume'])]['sticker'].to_list()
        print(f'The recommended watchlist for {self.trading_day} is the following list: {self.recommended_stickers}')



import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from joblib import Parallel, delayed
import logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = 'F:/tradingActionExperiments_database'

class yfPriceDatabaseBuilder:

    def __init__(self, start_date, nasdaq_screener = 'nasdaq_screener_20231007.csv', low_last_sale = 5, upper_last_sale=400):
        self.date = start_date
        self.date_dt = datetime.strptime(self.date, '%Y-%m-%d')
        self.db_path = f'{DB_PATH}/daywise_database'
        self.mod_date = self.date.replace('-', '_')
        self.instance_dir_name = f'stock_prices_for_{self.mod_date}'
        self.screener_file = nasdaq_screener
        self.lower_last_sale_price = low_last_sale
        self.upper_last_sale_price = upper_last_sale
        self.sticker_screener_parameter = f'screener_file: {self.screener_file}, lower last sale price boundary: {self.lower_last_sale_price}, upper last sale price boundary: {self.upper_last_sale_price}'

    def initialize_date_dir(self):
        if self.instance_dir_name not in os.listdir(self.db_path):
            instance_dir = f'{self.db_path}/{self.instance_dir_name}'
            os.mkdir(instance_dir)
        else:
            self.instance_dir = f'{self.db_path}/{self.instance_dir_name}'
            print(f'{self.instance_dir_name} is already created at the {self.db_path}!')

    def get_nasdaq_stickers(self):
        daily_nasdaq_stickers = pd.read_csv(f'{PROJ_PATH}/data_store/{self.screener_file}')
        daily_nasdaq_stickers.columns = \
            ['sticker', 'name', 'last_sale', 'net_change', 'change_perc', 'market_cap', 'country', 'ipo_year', 'volume', 'sector', 'industry']
        daily_nasdaq_stickers['last_sale'] = daily_nasdaq_stickers['last_sale'].str.lstrip('$').astype(float)
        daily_nasdaq_stickers['change_perc'] = daily_nasdaq_stickers['change_perc'].str.rstrip('%').astype(float)
        daily_nasdaq_stickers['ipo_year'] = daily_nasdaq_stickers['ipo_year'].astype('Int64')
        lower_last_sale_filt = (self.lower_last_sale_price < daily_nasdaq_stickers['last_sale'])
        upper_last_sale_filt = (daily_nasdaq_stickers['last_sale'] < self.upper_last_sale_price)
        daily_nasdaq_stickers = daily_nasdaq_stickers[lower_last_sale_filt & upper_last_sale_filt]
        self.stickers = list(daily_nasdaq_stickers['sticker'].unique())

    def load_individual_sticker_price_data(self, sticker):
        successfull_stickers = list()
        failed_stickers = list()
        try:
            sticker_data = yf.download(sticker,
                                       start=self.date_dt,
                                       end=self.date_dt + timedelta(1),
                                       interval='1m',
                                       progress=False)
            sticker_data.columns = [c.lower() for c in sticker_data.columns]
            if len(sticker_data) > 0:
                sticker_data.to_csv(f'{self.instance_dir_name}/{sticker}.csv')
                successfull_stickers.append(sticker)
            else:
                pass
                failed_stickers.append(sticker)
        except:
            pass
            failed_stickers.append(sticker)
        return (successfull_stickers, failed_stickers)

    def run_paralelle_loading(self):
        print(self.stickers)
        s = Parallel(n_jobs=16)(delayed(self.load_individual_sticker_price_data)(sticker) for sticker in self.stickers)
        log_df = pd.DataFrame.from_records(s, columns=['loaded_stickers', 'failed_stickers'])
        log_df['date'] = self.date
        return  log_df
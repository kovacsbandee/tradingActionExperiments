import os
import pandas as pd
from datetime import datetime
from utils.download_yf_stock_data import yfPriceDatabaseBuilder



PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = f'F:/tradingActionExperiments_database'


start_date = '2023-09-11'
day_nums = 1

log_dfs = list()
for loading_day in [loading_day.strftime('%Y-%m-%d') for loading_day in pd.bdate_range(pd.to_datetime(start_date, format='%Y-%m-%d'), periods=day_nums).to_list()]:
    if datetime.strptime(loading_day, '%Y-%m-%d').strftime('%A') != 'Sunday' or datetime.strptime(loading_day, '%Y-%m-%d').strftime('%A') != 'Saturday':
        db_builder = yfPriceDatabaseBuilder(start_date=loading_day)
        if db_builder.instance_dir_name not in os.listdir(db_builder.db_path):
            instance_dir = f'{db_builder.db_path}/{db_builder.instance_dir_name}'
            os.mkdir(instance_dir)
        else:
            db_builder.instance_dir = f'{db_builder.db_path}/{db_builder.instance_dir_name}'
            print(f'{db_builder.instance_dir_name} is already created at the {db_builder.db_path}!')
        db_builder.get_nasdaq_stickers()
        df = db_builder.run_paralelle_loading()

del sticker_data

import yfinance as yf
from datetime import timedelta
start_date = '2023-09-11'
sticker_data = yf.download('AAPL',
                           start=datetime.strptime(start_date, '%Y-%m-%d'),
                           end=datetime.strptime(start_date, '%Y-%m-%d') + timedelta(1),
                           interval='1m',
                           progress=False)



def get_all_listed_stickers_for_db():
    from utils.download_yf_stock_data import yfPriceDatabaseBuilder
    builder = yfPriceDatabaseBuilder(start_date='2023-09-11')
    builder.get_nasdaq_stickers()
    return builder.stickers

#stickers = get_all_listed_stickers_for_db()

def create_stockwise_price_data(sticker_csv):
    sticker_dfs = list()
    for daily_dirs in os.listdir(f'{DB_PATH}/daywise_database'):
        if sticker_csv in os.listdir(f'{DB_PATH}/daywise_database/{daily_dirs}/csvs'):
            sticker_dfs.append(pd.read_csv(f'{DB_PATH}/daywise_database/{daily_dirs}/csvs/{sticker_csv}'))
    if len(sticker_dfs) > 0:
        long_sticker_df = pd.concat(sticker_dfs, axis=0)
        long_sticker_df.set_index('Datetime', inplace=True)
        long_sticker_df.to_csv(f'{DB_PATH}/stockwise_database/{sticker_csv}')
    return sticker_csv
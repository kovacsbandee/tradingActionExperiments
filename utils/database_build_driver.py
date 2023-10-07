import os
import pandas as pd
from datetime import datetime
from utils.download_yf_stock_data import yfPriceDatabaseBuilder

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

import os
import json
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from joblib import Parallel, delayed
import logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

class yfPriceDatabaseBuilder:

    def __init__(self, start_date, nasdaq_screener = 'nasdaq_symbols_original.csv', low_last_sale = 5, upper_last_sale=400):
        self.date = start_date
        self.date_dt = datetime.strptime(self.date, '%Y-%m-%d')
        self.db_path = f'F:/tradingActionExperiments_database/daywise_database'
        self.mod_date = self.date.replace('-', '_')
        self.instance_dir_name = f'stock_prices_for_{self.mod_date}'
        self.screener_file = nasdaq_screener
        self.lower_last_sale_price = low_last_sale
        self.upper_last_sale_price = upper_last_sale
        self.symbol_screener_parameter = f'screener_file: {self.screener_file}, lower last sale price boundary: {self.lower_last_sale_price}, upper last sale price boundary: {self.upper_last_sale_price}'

    def initialize_date_dir(self):
        if self.instance_dir_name not in os.listdir(self.db_path):
            instance_dir = f'{self.db_path}/{self.instance_dir_name}'
            os.mkdir(instance_dir)
        else:
            self.instance_dir = f'{self.db_path}/{self.instance_dir_name}'
            print(f'{self.instance_dir_name} is already created at the {self.db_path}!')

    def get_nasdaq_symbols(self):
        daily_nasdaq_symbols = pd.read_csv(f'F:/tradingActionExperiments/src_tr/main/data_sources/{self.screener_file}')
        daily_nasdaq_symbols.columns = \
            ['symbol', 'name', 'last_sale', 'net_change', 'change_perc', 'market_cap', 'country', 'ipo_year', 'volume', 'sector', 'industry']
        daily_nasdaq_symbols['last_sale'] = daily_nasdaq_symbols['last_sale'].str.lstrip('$').astype(float)
        daily_nasdaq_symbols['change_perc'] = daily_nasdaq_symbols['change_perc'].str.rstrip('%').astype(float)
        daily_nasdaq_symbols['ipo_year'] = daily_nasdaq_symbols['ipo_year'].astype('Int64')
        lower_last_sale_filt = (self.lower_last_sale_price < daily_nasdaq_symbols['last_sale'])
        upper_last_sale_filt = (daily_nasdaq_symbols['last_sale'] < self.upper_last_sale_price)
        daily_nasdaq_symbols = daily_nasdaq_symbols[lower_last_sale_filt & upper_last_sale_filt]
        self.symbols = list(daily_nasdaq_symbols['symbol'].unique())

    def load_individual_symbol_price_data(self, symbol):
        successfull_symbols = list()
        failed_symbols = list()
        try:
            symbol_data = yf.download(symbol,
                                       start=self.date_dt,
                                       end=self.date_dt + timedelta(1),
                                       interval='1m',
                                       progress=False)
            symbol_data.columns = [c.lower() for c in symbol_data.columns]
            if len(symbol_data) > 0:
                symbol_data.to_csv(f'{self.instance_dir_name}/{symbol}.csv')
                successfull_symbols.append(symbol)
            else:
                pass
                failed_symbols.append(symbol)
        except:
            pass
            failed_symbols.append(symbol)
        return (successfull_symbols, failed_symbols)

    def run_paralelle_loading(self):
        print(self.symbols)
        s = Parallel(n_jobs=16)(delayed(self.load_individual_symbol_price_data)(symbol) for symbol in self.symbols)
        log_df = pd.DataFrame.from_records(s, columns=['loaded_symbols', 'failed_symbols'])
        log_df['date'] = self.date
        return  log_df

def build_daywise_directories(start_date, day_nums):
    log_dfs = list()
    for loading_day in [loading_day.strftime('%Y-%m-%d') for loading_day in pd.bdate_range(pd.to_datetime(start_date, format='%Y-%m-%d'), periods=day_nums).to_list()]:
        if datetime.strptime(loading_day, '%Y-%m-%d').strftime('%A') != 'Sunday' or datetime.strptime(loading_day, '%Y-%m-%d').strftime('%A') != 'Saturday':
            db_builder = yfPriceDatabaseBuilder(start_date=loading_day)
            if db_builder.instance_dir_name not in os.listdir(db_builder.db_path):
                instance_dir = f'{db_builder.db_path}/{db_builder.instance_dir_name}'
                os.mkdir(instance_dir)
                os.mkdir(f'{instance_dir}/csvs')
                db_builder.instance_dir_name = f'{instance_dir}/csvs'
            else:
                db_builder.instance_dir_name = f'{db_builder.db_path}/{db_builder.instance_dir_name}/csvs'
                print(f'{db_builder.instance_dir_name} is already created at the {db_builder.db_path}!')
            db_builder.get_nasdaq_symbols()
            df = db_builder.run_paralelle_loading()
            log_dfs.append(df)
    return log_dfs

def get_daywise_common_files(mode='write'):
    folds_df = pd.DataFrame({'folders': os.listdir(f'F:/tradingActionExperiments_database/daywise_database')})
    folds_df['prev_day_folders'] = folds_df['folders'].shift(1)
    folds_df = folds_df[1:]
    day_prev_day_folders = list(zip(folds_df['folders'], folds_df['prev_day_folders']))
    common_files = list()
    for folds in day_prev_day_folders:
        day_prev_day_files = dict()
        day_prev_day_files['day'] = folds[0]
        day_prev_day_files['prev_day'] = folds[1]
        prev_day_files = os.listdir(f'F:/tradingActionExperiments_database/daywise_database/{folds[1]}/csvs')
        files = list()
        for file in os.listdir(f'F:/tradingActionExperiments_database/daywise_database/{folds[0]}/csvs'):
            if (file in prev_day_files and 'sdf' not in file) and \
               (file in prev_day_files and 'normalized' not in file) and \
               (file in prev_day_files and 'w_' not in file):
                files.append(file)
        day_prev_day_files['common_files'] = files
        common_files.append(day_prev_day_files)
    if mode == 'write':
        import json as local_json
        with open(f'F:/tradingActionExperiments_database/daywise_common_files.json', 'w') as fout:
            for ddict in common_files:
                jout = local_json.dumps(ddict) + '\n'
                fout.write(jout)
    if mode == 'return':
        return common_files

def create_stockwise_price_data(symbol_csvs):
    for i, symbol_csv in enumerate(symbol_csvs):
        print(i, symbol_csv)
        symbol_dfs = list()
        for daily_dirs in os.listdir(f'F:/tradingActionExperiments_database/daywise_database'):
            if symbol_csv in os.listdir(f'F:/tradingActionExperiments_database/daywise_database/{daily_dirs}/csvs'):
                print(daily_dirs)
                symbol_dfs.append(pd.read_csv(f'F:/tradingActionExperiments_database/daywise_database/{daily_dirs}/csvs/{symbol_csv}'))
        if len(symbol_dfs) > 10:
            long_symbol_df = pd.concat(symbol_dfs, axis=0)
            long_symbol_df.set_index('Datetime', inplace=True)
            long_symbol_df.to_csv(f'F:/tradingActionExperiments_database/stockwise_database/{symbol_csv}')


def get_possible_local_yf_trading_days():
    file = open('F:/tradingActionExperiments_database/daywise_common_files.json')
    data = file.readlines()
    file.close()
    daywise_common_files = [json.loads(l) for l in data]
    trading_days = [datetime.strptime(d['day'][17:], '%Y_%m_%d') for d in daywise_common_files]
    scanning_day = [datetime.strptime(d['prev_day'][17:], '%Y_%m_%d') for d in daywise_common_files]
    return trading_days, scanning_day


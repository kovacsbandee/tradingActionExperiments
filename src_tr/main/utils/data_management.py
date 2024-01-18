import os
import pandas as pd
import json


class DataManager:

    def __init__(self,
                 trading_day,
                 scanning_day,
                 run_id,
                 db_path):
        self.trading_day = trading_day
        self.scanning_day = scanning_day
        self.run_id = run_id
        self.db_path = db_path
        self.daily_dir_name = self.run_id + '_' + 'trading_day' + '_' + self.trading_day.strftime('%Y_%m_%d')

    def create_daily_dirs(self):
        '''
        ebben a mappában lesz a paraméter json
        a pre_market_stats
        a post_trading_stats
        és a symbol_df-ből a program futásának végén generált csv-ket és plot-okat tartalmazó mappa
        '''
        daily_symbol_dir_name = 'daily_files'
        if self.daily_dir_name not in os.listdir(self.db_path):
            os.mkdir(f'{self.db_path}/{self.daily_dir_name}')
            os.mkdir(f'{self.db_path}/{self.daily_dir_name}/{daily_symbol_dir_name}')
            os.mkdir(f'{self.db_path}/{self.daily_dir_name}/{daily_symbol_dir_name}/csvs')
            os.mkdir(f'{self.db_path}/{self.daily_dir_name}/{daily_symbol_dir_name}/plots')
            print(f'daily data store is created with the name: ', self.daily_dir_name)
        else:
            print(f'{self.daily_dir_name} already exists with this run ID, change the run ID fella!')

    def save_params_and_scanner_output(self, params, scanner_output):
        self.run_parameters = params
        self.scanner_output = scanner_output
        with open(f'{self.db_path}/{self.daily_dir_name}/run_paramters.json', 'w') as fp:
            json.dump(self.run_parameters, fp)
        self.scanner_output.to_csv(f'{self.db_path}/{self.daily_dir_name}/recommended_symbols_pre_market_stats.csv', index=False)
        print(f'run_parameters and scanner output was successfully saved')

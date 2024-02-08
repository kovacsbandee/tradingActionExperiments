import os
import pandas as pd
import json
import shutil
from src_tr.main.utils.plots import plot_daily_statistics_correlation_matrix, plot_daily_statistics, daily_time_series_charts

class DataManager:

    def __init__(self,
                 data_source,
                 trading_day,
                 scanning_day,
                 run_id,
                 db_path):
        self.data_source = data_source
        self.trading_day = trading_day
        self.scanning_day = scanning_day
        self.run_id = run_id
        self.db_path = db_path
        self.daily_dir_name = 'trading_day' + '_' + self.trading_day.strftime('%Y_%m_%d')

    def create_daily_dirs(self):
        '''
        ebben a mappában lesz a paraméter json
        a pre_market_stats
        a post_trading_stats
        és a symbol_df-ből a program futásának végén generált csv-ket és plot-okat tartalmazó mappa
        '''
        daily_symbol_dir_name = 'daily_files'
        if self.run_id not in os.listdir(f'{self.db_path}/output/'):
            os.mkdir(f"{self.db_path}/output/{self.run_id}")
        if self.daily_dir_name in os.listdir(f'{self.db_path}/output/{self.run_id}'):
            os.mkdir(f"{self.db_path}/output/{self.run_id}/{self.daily_dir_name}")
            os.mkdir(f"{self.db_path}/output/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}")
            os.mkdir(f"{self.db_path}/output/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}/csvs")
            os.mkdir(f"{self.db_path}/output/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}/plots")

            # shutil.rmtree(f"{self.db_path}/output/{self.run_id}")
            # print('Previous directory was deleted and a new one was created.')
        print(f"daily data store was created with the name: {self.daily_dir_name}")

    def save_params(self, params):
        '''
        Saves the parameters describing the run as as json.
        '''
        self.run_parameters = params
        with open(f"{self.db_path}/output/{self.run_id}/run_paramters.json", 'w') as fp:
            json.dump(self.run_parameters, fp)
        print("run_parameters was successfully saved")

    def save_daily_statistics_and_aggregated_plots(self, recommended_symbols, symbol_dict):
        '''

        '''
        daily_stats_for_all_symbols = list()
        for symbol in symbol_dict.keys():
            daily_df = symbol_dict[symbol]['daily_price_data_df']

            daily_stats = dict()
            daily_stats['symbol'] = symbol
            daily_stats['last_capital_td'] = daily_df[(daily_df['current_capital'] >= 1.0) & (~daily_df['current_capital'].isna())]['current_capital'][-1]
            daily_stats['baseline_yield_perc_td'] = (daily_stats['last_capital_td'] / (self.run_parameters['init_cash'] * (daily_df['o'][-1] / daily_df['o'][0])) - 1) * 100
            daily_stats['last_yield_perc_td'] = ((daily_df[(daily_df['current_capital'] >= 1.0) & \
                                                        (~daily_df['current_capital'].isna())]['current_capital'][-1] / self.run_parameters['init_cash']) - 1) * 100
            daily_stats['avg_yield_perc_td'] = ((daily_df[(daily_df['current_capital'] >= 1.0)]['current_capital'].mean() / self.run_parameters['init_cash']) - 1) * 100
            daily_stats['max_yield_perc_td'] = ((daily_df['current_capital'].max() / self.run_parameters['init_cash']) - 1) * 100
            daily_stats['min_yield_perc_td'] = ((daily_df[(daily_df['current_capital'] >= 1.0)]['current_capital'].min() / self.run_parameters['init_cash']) - 1) * 100

            daily_stats['avg_capital_td'] = daily_df[daily_df['current_capital'] > self.run_parameters['init_cash']*0.1]['current_capital'].mean()
            daily_stats['min_capital_td'] = daily_df[(daily_df['current_capital'] >= 1.0)]['current_capital'].min()
            daily_stats['max_capital_td'] = daily_df['current_capital'].max()
            daily_stats['max_time_stamp_td'] = daily_df['current_capital'].idxmax()
            daily_stats['in_position_percent_td'] = (len(daily_df[daily_df['position'] != 'out']) / len(daily_df)) * 100
            # az alábbi néhánynak szerepelelnie kéne a scanner statisztikák között is
            daily_stats['bull_candle_ratio_td'] = len(daily_df[daily_df['c'] > daily_df['o']]) / len(daily_df)
            daily_stats['bear_candle_ratio_td'] = len(daily_df[daily_df['c'] < daily_df['o']]) / len(daily_df)
            daily_stats['bull_per_bear_ratio_td'] = daily_stats['bull_candle_ratio_td'] / daily_stats['bear_candle_ratio_td']
            daily_stats['daily_high_max_td'] = daily_df['h'].max()
            daily_stats['low_min_td'] = daily_df['l'].min()

            daily_stats_for_all_symbols.append(daily_stats)

        daily_stats_for_all_symbols = pd.DataFrame(daily_stats_for_all_symbols)

        self.total_recommended_symbol_statistics = pd.merge(daily_stats_for_all_symbols, recommended_symbols, on='symbol', how='left')
        self.total_recommended_symbol_statistics.sort_values(by=['last_yield_perc_td'], inplace=True, ascending=False)
        plot_daily_statistics(plot_df=self.total_recommended_symbol_statistics, db_path=self.db_path, run_id=self.run_id, daily_dir_name=self.daily_dir_name)
        plot_daily_statistics_correlation_matrix(plot_df=self.total_recommended_symbol_statistics, db_path=self.db_path, run_id=self.run_id, daily_dir_name=self.daily_dir_name)
        self.total_recommended_symbol_statistics.to_csv(f"{self.db_path}/output/{self.run_id}/{self.daily_dir_name}/recommended_symbols_sd_td_market_stats.csv", index=False)
        print("Statistics, and daily statistics plots are successfully saved.")

    def save_daily_charts(self, symbol_dict):
        date = self.trading_day.strftime('%Y_%m_%d')
        daily_time_series_charts(symbol_dict,
                                 date = date,
                                 epsilon = self.run_parameters['epsilon'],
                                 data_source=self.data_source,
                                 db_path = self.db_path,
                                 run_id=self.run_id,
                                 daily_dir_name = self.daily_dir_name)
        print('Daily charts were written out successfully.')
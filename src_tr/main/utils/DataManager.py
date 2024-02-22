import os
import pandas as pd
import json
import shutil
from src_tr.main.utils.plots import plot_daily_statistics_correlation_matrix, plot_daily_statistics, daily_time_series_charts
import logging

from config import config

class DataManager:

    def __init__(self,
                 mode,
                 trading_day,
                 scanning_day,
                 run_id):
        self.mode = mode
        self.trading_day = trading_day
        self.scanning_day = scanning_day
        self.run_id = run_id
        self.daily_dir_name = '_'.join([run_id, trading_day.strftime('%Y_%m_%d')])
        self.recommended_symbol_list = None

    def create_daily_dirs(self):
        if self.run_id not in os.listdir(config['output_stats']):
            os.mkdir(f"{config['output_stats']}/{self.run_id}")
            
        daily_symbol_dir_name = 'daily_files'
        if self.daily_dir_name in os.listdir(f"{config['output_stats']}/{self.run_id}"):
            shutil.rmtree(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}")
            logging.info('Previous directory was deleted and a new one was created.')

        os.mkdir(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}")
        os.mkdir(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}")
        os.mkdir(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}/csvs")
        os.mkdir(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}/plots")
        os.mkdir(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/{daily_symbol_dir_name}/scanner_stats")
        logging.info(f"daily data store was created with the name: {self.daily_dir_name}")

    def save_params(self, params):
        self.run_parameters = params
        with open(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/run_parameters.json", 'w') as fp:
            json.dump(self.run_parameters, fp)
        logging.info("run_parameters was successfully saved")

    def save_daily_statistics_and_aggregated_plots(self, recommended_symbols, symbol_dict):
        daily_stats_for_all_symbols = list()
        for symbol in symbol_dict.keys():
            daily_df = symbol_dict[symbol]['daily_price_data_df']

            daily_stats = dict()
            daily_stats['symbol'] = symbol
            daily_stats['last_capital_td'] = daily_df[(daily_df['current_capital'] >= 1.0) & (~daily_df['current_capital'].isna())]['current_capital'][-1]
            daily_stats['basline_yield_td'] = (self.run_parameters['init_cash'] * (daily_df['o'][-1] / daily_df['o'][0]))
            daily_stats['baseline_yield_perc_td'] = ((daily_stats['last_capital_td'] / (self.run_parameters['init_cash'] * (daily_df['o'][-1] / daily_df['o'][0]))) - 1) * 100
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

        self.total_recommended_symbol_statistics = pd.merge(recommended_symbols, daily_stats_for_all_symbols, on='symbol', how='left')
        self.total_recommended_symbol_statistics.sort_values(by=['last_yield_perc_td'], inplace=True, ascending=False)
        plot_daily_statistics(plot_df=self.total_recommended_symbol_statistics, db_path=f"{config['output_stats']}/{self.run_id}", daily_dir_name=self.daily_dir_name)
        plot_daily_statistics_correlation_matrix(plot_df=self.total_recommended_symbol_statistics, db_path=f"{config['output_stats']}/{self.run_id}", daily_dir_name=self.daily_dir_name)
        self.total_recommended_symbol_statistics.to_csv(f"{config['output_stats']}/{self.run_id}/{self.daily_dir_name}/recommended_symbols_sd_td_market_stats.csv", index=False)
        logging.info("Statistics, and daily statistics plots are successfully saved.")

    def save_daily_charts(self, symbol_dict):
        date = self.trading_day.strftime('%Y_%m_%d')
        daily_time_series_charts(symbol_dict,
                                 date = date,
                                 epsilon = self.run_parameters['epsilon'],
                                 mode=self.mode,
                                 db_path = f"{config['output_stats']}/{self.run_id}",
                                 daily_dir_name = self.daily_dir_name)
        logging.info('Daily charts were written out successfully.')
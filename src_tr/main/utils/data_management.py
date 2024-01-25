import os
import pandas as pd
import json
import shutil
from src_tr.main.utils.plots import plot_daily_statistics_correlation_matrix, plot_daily_statistics, create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments

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
        if self.daily_dir_name in os.listdir(self.db_path):
            shutil.rmtree(f'{self.db_path}/{self.daily_dir_name}')
            print('Previous directory was deleted and a new one was created.')

        os.mkdir(f'{self.db_path}/{self.daily_dir_name}')
        os.mkdir(f'{self.db_path}/{self.daily_dir_name}/{daily_symbol_dir_name}')
        os.mkdir(f'{self.db_path}/{self.daily_dir_name}/{daily_symbol_dir_name}/csvs')
        os.mkdir(f'{self.db_path}/{self.daily_dir_name}/{daily_symbol_dir_name}/plots')
        print(f'daily data store was created with the name: ', self.daily_dir_name)

    def save_params(self, params):
        '''
        Saves the parameters describing the run as as json.
        '''
        self.run_parameters = params
        with open(f'{self.db_path}/{self.daily_dir_name}/run_paramters.json', 'w') as fp:
            json.dump(self.run_parameters, fp)
        print(f'run_parameters was successfully saved')

    def save_daily_statistics_and_aggregated_plots(self, recommended_symbols, symbol_dict):
        '''

        '''
        daily_stats_for_all_symbols = list()
        for symbol in symbol_dict.keys():
            daily_df = symbol_dict[symbol]['daily_price_data_df']

            daily_stats = dict()
            daily_stats['symbol'] = symbol
            daily_stats['avg_capital_td'] = daily_df[daily_df['current_capital'] > self.run_parameters['init_cash']*0.1]['current_capital'].mean()
            daily_stats['min_capital_td'] = daily_df['current_capital'].min()
            daily_stats['max_capital_td'] = daily_df['current_capital'].max()
            daily_stats['max_per_input_cap_ratio_td'] = daily_df['current_capital'].max() / self.run_parameters['init_cash']
            daily_stats['in_position_percent_td'] = (len(daily_df[daily_df['position'] != 'out']) / len(daily_df)) * 100
            # az alábbi néhány szerepel a scanner statisztikák között is
            daily_stats['bear_candle_ratio_td'] = len(daily_df[daily_df['c'] < daily_df['o']]) / len(daily_df)
            daily_stats['bull_candle_ratio_td'] = len(daily_df[daily_df['c'] > daily_df['o']]) / len(daily_df)
            daily_stats['daily_high_max_td'] = daily_df['h'].max()
            daily_stats['low_min_td'] = daily_df['l'].min()
            daily_stats_for_all_symbols.append(daily_stats)

        daily_stats_for_all_symbols = pd.DataFrame(daily_stats_for_all_symbols)

        self.total_recommended_symbol_statistics = pd.merge(recommended_symbols, daily_stats_for_all_symbols, on='symbol', how='left')
        self.total_recommended_symbol_statistics.sort_values(by=['max_per_input_cap_ratio_td'], inplace=True, ascending=False)
        plot_daily_statistics(plot_df=self.total_recommended_symbol_statistics, db_path=self.db_path, daily_dir_name=self.daily_dir_name)
        plot_daily_statistics_correlation_matrix(plot_df=self.total_recommended_symbol_statistics, db_path=self.db_path, daily_dir_name=self.daily_dir_name)
        self.total_recommended_symbol_statistics.to_csv(f'{self.db_path}/{self.daily_dir_name}/recommended_symbols_sd_td_market_stats.csv', index=False)
        print(f'Statistics, and daily statistics plots are successfully saved.')

    def save_daily_charts(self, symbol_dict):
        date = self.trading_day.strftime('%Y_%m_%d')
        create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(symbol_dict,
                                                                                      date = date,
                                                                                      epsilon = self.run_parameters['epsilon'],
                                                                                      db_path = self.db_path,
                                                                                      daily_dir_name = self.daily_dir_name)
        print('Daily charts were written out successfully.')
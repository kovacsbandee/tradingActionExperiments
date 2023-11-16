'''
In this file various metrics and plots are created to support the analysis of the experiments.
A generalized stickerwise framework has to be defined for all strategies based on gains, general trends, indicator stats, zero crossings,
price range and volatility measures.
'''

import pandas as pd
import numpy as np
from scipy.stats import skewtest
import os
from joblib import Parallel, delayed
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def compare_results(loser_df,winners_df, indicator_price, plot_name=''):
    vars = ['cap_max', 'cap_min', 'cap_mean', f'{indicator_price}_max', f'{indicator_price}_min', f'{indicator_price}_mean', f'{indicator_price}_std', f'{indicator_price}_max',
            f'{indicator_price}_min', f'{indicator_price}_mean', f'{indicator_price}_std', 'high_max', 'high_min', 'high_std', 'low_max', 'low_min', 'low_std',
            'price_range_hl', 'price_range_oc', 'volume_max', 'volume_min', 'volume_mean', f'{indicator_price}_small_normalized_indicator_col_max',
            f'{indicator_price}_small_normalized_indicator_col_min', f'{indicator_price}_small_normalized_indicator_col_mean',
            f'{indicator_price}_big_normalized_indicator_col_max', f'{indicator_price}_big_normalized_indicator_col_min', f'{indicator_price}_big_normalized_indicator_col_mean']
    fig = make_subplots(cols=1,
                        subplot_titles=vars,
                        rows=len(vars))

    for i, v in enumerate(vars):
        fig.add_trace(go.Histogram(x=loser_df[v],
                                   name='losers',
                                   nbinsx=100,
                                   showlegend=True if i == 0 else False,
                                   histnorm='probability density',
                                   marker = dict(color='blue')), col=1, row=i + 1)
        fig.add_trace(go.Histogram(x=winners_df[v],
                                   name='winners',
                                   nbinsx=100,
                                   showlegend=True if i==0 else False,
                                   histnorm='probability density',
                                   marker = dict(color='red')), col=1, row=i + 1)
    fig.update_layout(barmode='overlay',
                      height=len(vars)*150)
    fig.update_traces(opacity=0.5)
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/losers_and_mean_winner_comparision_{plot_name}.html')


def get_stats_from_results(file_name,
                           indicator_price,
                           lower_price_boundary=10,
                           upper_price_boundary = 400,
                           avg_volume_cond = 25000,
                           std_close_lower_boundary_cond = 0.25,
                           epsilon = 0.01):
    results = pd.read_csv(f'F:/tradingActionExperiments/data_store/{file_name}')
    results = results[(results['volume_max'] != 0)]
    results = results[(~results[f'{indicator_price}_small_ind_col_max'].isna())]
    scanner_check = results.copy()
    scanner_check['filter_col'] = scanner_check['sticker'] + scanner_check['day']
    scanner_in = scanner_check[(scanner_check[f'{indicator_price}_mean'] > lower_price_boundary) & \
                               (scanner_check[f'{indicator_price}_mean'] < upper_price_boundary) & \
                               (scanner_check['volume_mean'] > avg_volume_cond) & \
                               (scanner_check[f'{indicator_price}_std'] > std_close_lower_boundary_cond) & \
                               (scanner_check[f'{indicator_price}_small_normalized_indicator_col_mean'] > epsilon) & \
                               (scanner_check[f'{indicator_price}_big_normalized_indicator_col_mean'] > epsilon)]
    scanner_out = scanner_check[~scanner_check['filter_col'].isin(scanner_in['filter_col'].unique())]
    max_winners = results[results['cap_max'] > 25050].copy()
    mean_winners = results[results['cap_mean'] > 25050].copy()
    losers = results[results['cap_max'] == 25000].copy()

    print('Az eredmény file neve: ', file_name)
    print('Scanner in skewness', skewtest(scanner_in.cap_mean).statistic)
    print('Scanner out skewness', skewtest(scanner_out.cap_mean).statistic)
    print('in cap mean', scanner_in.cap_mean.mean())
    print('out cap mean', scanner_out.cap_mean.mean())
    print('Azon napok és részvények számának aránya a teljes mintában, amelyeknél 25050-nél nagyobb volt a maximális hoztam',max_winners.shape[0] / results.shape[0])
    print('Azon napok és részvények számának aránya a teljes mintában, amelyeknél 25050-nél nagyobb volt az átlagos hoztam',mean_winners.shape[0] / results.shape[0])
    print('Azon minták, ahol a cap_max nagyobb mint 25050, ott a cap_min is nagyobb!')
    print('Azon napok és részvények számának aránya a teljes mintában, amelyek veszteségesek voltak',losers.shape[0] / results.shape[0])
    return scanner_check, losers, max_winners, mean_winners


def analyse_in_respect_of_total_period(w_or_l_df,
                                       res_df,
                                       occ_freq=14):
    occurance_freq = w_or_l_df.groupby(by='sticker').count().sort_values(by='day', ascending=False).reset_index()
    occurance_freq = occurance_freq[['sticker', 'day']]
    occurance_freq.columns = ['sticker', 'occurance_freq']
    result_analysis_df = pd.merge(w_or_l_df, occurance_freq, how='left', on='sticker')

    df = pd.merge(res_df, occurance_freq, how='right', on='sticker')
    df = df[df.occurance_freq > occ_freq].sort_values(by=['sticker', 'day'])
    df = pd.merge(df,
                  df[['sticker', 'cap_min', 'cap_mean', 'cap_max']].groupby(by=['sticker']).mean(). \
                  rename({'cap_min': 'cap_min_avg',
                          'cap_mean': 'cap_mean_avg',
                          'cap_max': 'cap_max_avg'}, axis='columns').reset_index(),
                  how='left',
                  on='sticker')
    df = df[['sticker', 'day', 'cap_max', 'cap_min', 'cap_mean', 'cap_min_avg', 'cap_mean_avg', 'cap_max_avg']]
    df['period_gain'] = df['cap_max'] - 25000
    tpg = df[['sticker', 'period_gain']].groupby(by='sticker').sum()
    tpg.sort_values(by='period_gain', ascending=True, inplace=True)
    print(tpg)
    print('Max period gain', tpg.period_gain.max())
    print('Min period gain', tpg.period_gain.min())
    print('Average period gain', tpg.period_gain.mean())
    print('Total number of days in period', len(df.day.unique()))
    return tpg


PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = 'F:/tradingActionExperiments_database'

#
# file_close = 'final_strategy_implementation_results_on_daily_w_price_ranges.csv'
# file_open = 'final_strategy_implementation_results_on_daily_w_price_ranges_w_ind_pirce_open.csv'
#
#
# close_results, close_losers, close_max_winners, close_mean_winners = get_stats_from_results(file_name=file_close, indicator_price='close')
# compare_results(loser_df=close_losers, winners_df=close_mean_winners, indicator_price='close', plot_name=f'{file_close}_mean')
# compare_results(loser_df=close_losers, winners_df=close_max_winners, indicator_price='close', plot_name=f'{file_close}_max')
# close_mean_tpg = analyse_in_respect_of_total_period(w_or_l_df = close_mean_winners,
#                                                    res_df = close_results,
#                                                    occ_freq  = 14)
#
# open_results, open_losers, open_max_winners, open_mean_winners = get_stats_from_results(file_name=file_open, indicator_price='open')
# compare_results(loser_df=open_losers, winners_df=open_mean_winners, indicator_price='open', plot_name=f'{file_open}_mean')
# compare_results(loser_df=open_losers, winners_df=open_max_winners, indicator_price='open', plot_name=f'{file_open}_max')
# open_mean_tpg = analyse_in_respect_of_total_period(w_or_l_df = open_mean_winners,
#                                                    res_df = open_results,
#                                                    occ_freq  = 14)
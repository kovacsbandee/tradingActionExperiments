import os
from itertools import chain

import pandas as pd
from joblib import Parallel, delayed
# from data_sources.add_indicators import add_rolling_average, add_MACD, add_gradient
# from strategies.strategy_for_mass_experiments import add_trendscalping_specific_indicators, apply_simple_combined_trendscalping_for_mass
# from strategies.strategy_for_mass_experiments import add_macd_and_trendscalping_indicators, apply_macd_enhanced_trendscalping

from strategies.strategy_driver import add_trendscalping_specific_indicators, create_strategy_filter, apply_strategy_w_stop_loss

PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = f'F:/tradingActionExperiments_database'

short_ma = 5
long_ma = 12
exp_desc = f'with_first_stop_loss_constraints_short_ma{short_ma}_long_ma{long_ma}'

def get_all_file_w_paths_for_daily():
    all_file = list(chain.from_iterable(
        [[f'{DB_PATH}/{dir}/csvs/{f}' for f in os.listdir(f'{DB_PATH}/{dir}/csvs') if all([l.isupper() for l in f.rstrip('.csv')])]
         for dir in os.listdir(DB_PATH)]))
    return all_file


def get_all_file_w_paths_for_stockwise():
    stickers = [csv.split('_')[0] for csv in os.listdir(f'{DB_PATH}/stockwise_database')]
    all_file = [f'{DB_PATH}/stockwise_database/{csv}' for csv in stickers if '.csv' in csv]
    return all_file


# def create_strategy_results(csv, exp_desc, short_ma, long_ma):
#     sticker_df = pd.read_csv(csv)
#     sticker_df = sticker_df[['Datetime' ,'open', 'high', 'low', 'close', 'adj close', 'volume']]
#     sticker_df.set_index('Datetime', inplace=True)
#     date = csv[65:75].replace('_', '-')
#     sticker = csv.split('/')[-1][:-4]
#     avg_close = sticker_df['close'].mean()
#     avg_volume = sticker_df['volume'].mean()
#     if len(sticker_df) < 195:
#         final_capital = 9999
#         total_gain = 9999
#     else:
#         sticker_df = add_trendscalping_specific_indicators(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
#         sticker_df = apply_simple_combined_trendscalping_for_mass(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
#         capitals = sticker_df[sticker_df['current_capital'] != 0.0]['current_capital']
#         final_capital = 0.0 if len(capitals) == 0 else capitals[-1]
#         total_gain = sticker_df['gain_per_position'].sum()
#     save_file_name = csv.rstrip('.csv') + '_' + exp_desc + '.csv'
#     sticker_df.to_csv(save_file_name, mode='w+')
#     result = [date, sticker, avg_close, avg_volume, final_capital, total_gain]
#     return result
#
#
# def create_strategy_results_macd_enhanced(csv, exp_desc=exp_desc, short_ma=short_ma, long_ma=long_ma):
#     sticker_df = pd.read_csv(csv)
#     sticker_df = sticker_df[['Datetime' ,'open', 'high', 'low', 'close', 'adj close', 'volume']]
#     sticker_df.set_index('Datetime', inplace=True)
#     date = csv[65:75].replace('_', '-')
#     sticker = csv.split('/')[-1][:-4]
#     avg_close = sticker_df['close'].mean()
#     avg_volume = sticker_df['volume'].mean()
#     if len(sticker_df) < 195:
#         final_capital = 9999
#         total_gain = 9999
#     else:
#         sticker_df = add_macd_and_trendscalping_indicators(df=sticker_df, ma_tscalp_short=short_ma, ma_tscalp_long=long_ma, short_macd=100, long_macd=220)
#         sticker_df = apply_macd_enhanced_trendscalping(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
#         capitals = sticker_df[sticker_df['current_capital'] != 0.0]['current_capital']
#         final_capital = 0.0 if len(capitals) == 0 else capitals[-1]
#         total_gain = sticker_df['gain_per_position'].sum()
#     save_file_name = csv.rstrip('.csv') + '_' + exp_desc + '.csv'
#     sticker_df.to_csv(save_file_name, mode='w+')
#     result = [date, sticker, avg_close, avg_volume, final_capital, total_gain]
#     return result


def create_strategy_results_w_stop_loss(csv, exp_desc=exp_desc, short_ma=5, long_ma=12):
    sticker_df = pd.read_csv(csv)
    sticker_df = sticker_df[['Datetime' ,'open', 'high', 'low', 'close', 'adj close', 'volume']]
    sticker_df.set_index('Datetime', inplace=True)
    date = csv[65:75].replace('_', '-')
    sticker = csv.split('/')[-1][:-4]
    avg_close = sticker_df['close'].mean()
    avg_volume = sticker_df['volume'].mean()
    if len(sticker_df) < 195:
        final_capital = 9999
        total_gain = 9999
    else:
        sticker_df = add_trendscalping_specific_indicators(sticker_df, averaged_cols=['close'], ma_short=short_ma, ma_long=long_ma)
        filts = create_strategy_filter(df=sticker_df, ind_price='close', ma_short=short_ma, ma_long=long_ma)
        sticker_df = apply_strategy_w_stop_loss(sticker_df, filters=filts)
        capitals = sticker_df[sticker_df['current_capital'] != 0.0]['current_capital']
        final_capital = 0.0 if len(capitals) == 0 else capitals[-1]
        total_gain = sticker_df['gain_per_position'].sum()
    save_file_name = csv.rstrip('.csv') + '_' + exp_desc + '.csv'
    sticker_df.to_csv(save_file_name, mode='w+')
    result = [date, sticker, avg_close, avg_volume, final_capital, total_gain]
    return result


def run_parallel_strategy_operations(all_csvs, exp_desc):
    results = list()
    for csv in all_csvs:
        res = create_strategy_results_w_stop_loss(csv=csv)
        results.append(res)
    # results = Parallel(n_jobs=16)(delayed(create_strategy_results_macd_enhanced)(csv) for csv in all_csvs)
    result_df = pd.DataFrame(results, columns=['date', 'sticker', 'avg_close', 'avg_volume', 'final_capital', 'total_gain'])
    result_df.to_csv(f'{PROJ_PATH}/data_store/results/{exp_desc}.csv')
    return result_df

all_csvs = get_all_file_w_paths_for_stockwise()
results = run_parallel_strategy_operations(all_csvs, exp_desc=exp_desc)


results = results[(results['final_capital'] != 0.0) & (results.final_capital != 9999) & (~results.sticker.str.contains('with'))].copy()
results.sort_values('final_capital', inplace=True)
results.to_csv(f'{PROJ_PATH}/data_store/results/results_{exp_desc}.csv')

results = pd.read_csv(f'{PROJ_PATH}/data_store/results/results_{exp_desc}.csv')

from plots.plots import create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments


sticker = 'AAPL'
sticker_csv = f'{sticker}.csv'
df = pd.read_csv(f'{DB_PATH}/stockwise_database/{sticker_csv}', index_col='Datetime')


for sticker in results[results['final_capital'] > 4500]['sticker']:
    sticker_csv = f'AAPL_{exp_desc}.csv'
    df = pd.read_csv(f'{DB_PATH}/stockwise_database/{sticker_csv}', index_col='Datetime')
    #df.rename(columns={'trading_action_x': 'trading_action'}, inplace=True)
    marker=create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(df,
                                                                                         plot_name=exp_desc,
                                                                                         sticker_name=sticker_csv,
                                                                                         indicators=['position',
                                                                                                     'current_capital',
                                                                                                     'gain_per_position'])


'''
Stratégia ötlet:
nincsen wathclist, de a néhány órás MACD-t számoljuk, ahol a MACD pozitív, ott a long trendscalping stratégiát használjuk, ahol negatív, ott a short-ot

# MACD feltétel, minden kereskedési nap, minden órájából legyen legalább 1 mérés
price = 'close'
short_macd = 120
long_macd = 260

full_range = list(pd.read_csv(f'{DB_PATH}/stockwise_database/AMZN.csv', index_col='Datetime').index.str.split(':').str.get(0).unique())

sticker_csv = [f for f in os.listdir(f'{DB_PATH}/stockwise_database')][40]

sticker_csv = 'AAPL.csv'
df = pd.read_csv(f'{DB_PATH}/stockwise_database/{sticker_csv}', index_col='Datetime')


#if len(set(df.index.str.split(':').str.get(0).unique())) / len(set(full_range)) > 0.8:
# apply macd
# df.index = pd.DatetimeIndex(df.index)
# df = \
# pd.merge(df,
#          df.groupby([df.index.year, df.index.month, df.index.day, df.index.hour])[price].mean(),
#          how='left',
#          left_on=[df.index.year, df.index.month, df.index.day, df.index.hour],
#          right_index=True)
# df.rename(columns={'close_y': f'day_hour_{price}_agg'}, inplace=True)
df[f'macd_{short_macd}_{long_macd}'] = add_MACD(df, col=price, short_macd=short_macd, long_macd=long_macd)
df[f'macd_{short_macd}_{long_macd}_grad'] = add_gradient(df, col=f'macd_{short_macd}_{long_macd}')
df[f'macd_{short_macd}_{long_macd}_grad_ma'] = add_rolling_average(df, f'macd_{short_macd}_{long_macd}_grad', window_length=60)
df[f'macd_{short_macd}_{long_macd}_grad2'] = add_gradient(df, col=f'macd_{short_macd}_{long_macd}_grad')
df[f'macd_{short_macd}_{long_macd}_grad2'] = df[f'macd_{short_macd}_{long_macd}_grad2']*10000
df[f'macd_{short_macd}_{long_macd}_grad2_ma'] = add_rolling_average(df, f'macd_{short_macd}_{long_macd}_grad2', window_length=20)
df.loc[df[f'macd_{short_macd}_{long_macd}_grad_ma'] < 0, 'long_short_sign'] = -1
df.loc[df[f'macd_{short_macd}_{long_macd}_grad_ma'] > 0, 'long_short_sign'] = 1

# else:
#     pass

from plots.plots import create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments

create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(df, sticker_name=sticker_csv, indicators=['long_short_sign',
                                                                                                                        f'macd_{short_macd}_{long_macd}_grad_ma'])
'''

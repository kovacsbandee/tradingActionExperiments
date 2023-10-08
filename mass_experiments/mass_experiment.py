import os
from itertools import chain

import pandas as pd
from joblib import Parallel, delayed
from data_sources.add_indicators import add_rolling_average, add_MACD, add_gradient
from strategies.strategy_for_mass_experiments import add_strategy_specific_indicators, apply_simple_combined_trend_following_strategy


PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = f'F:/tradingActionExperiments_database'


def get_all_file_w_paths():
    all_file = list(chain.from_iterable(
        [[f'{DB_PATH}/{dir}/csvs/{f}' for f in os.listdir(f'{DB_PATH}/{dir}/csvs') if all([l.isupper() for l in f.rstrip('.csv')])]
         for dir in os.listdir(DB_PATH)]))
    return all_file


def create_strategy_results(csv, exp_desc, short_ma, long_ma):
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
        sticker_df = add_strategy_specific_indicators(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
        sticker_df = apply_simple_combined_trend_following_strategy(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
        capitals = sticker_df[sticker_df['current_capital'] != 0.0]['current_capital']
        final_capital = 0.0 if len(capitals) == 0 else capitals[-1]
        total_gain = sticker_df['gain_per_position'].sum()
    save_file_name = csv.rstrip('.csv') + '_' + exp_desc + '.csv'
    sticker_df.to_csv(save_file_name, mode='w+')
    result = [date, sticker, avg_close, avg_volume, final_capital, total_gain]
    return result

def run_parallel_strategy_operations(all_csvs, exp_desc):
    # results = list()
    # for csv in all_csvs:
    #     res = create_strategy_results(csv=csv)
    #     results.append(res)
    results = Parallel(n_jobs=16)(delayed(create_strategy_results)(csv) for csv in all_csvs)
    result_df = pd.DataFrame(results, columns=['date', 'sticker', 'avg_close', 'avg_volume', 'final_capital', 'total_gain'])
    result_df.to_csv(f'{PROJ_PATH}/data_store/results/{exp_desc}.csv')
    return result_df

def get_all_listed_stickers_for_db():
    from utils.download_yf_stock_data import yfPriceDatabaseBuilder
    builder = yfPriceDatabaseBuilder(start_date='2023-09-11')
    builder.get_nasdaq_stickers()
    return builder.stickers

stickers = get_all_listed_stickers_for_db()

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


results = Parallel(n_jobs=16)(delayed(create_stockwise_price_data)(csv) for csv in [f'{s}.csv' for s in stickers])

# MACD feltétel, minden kereskedési nap, minden órájából legyen legalább 1 mérés
price = 'close'
short_macd = 120
long_macd = 260

full_range = list(pd.read_csv(f'{DB_PATH}/stockwise_database/AMZN.csv', index_col='Datetime').index.str.split(':').str.get(0).unique())

sticker_csv = [f for f in os.listdir(f'{DB_PATH}/stockwise_database')][40]

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
df[f'macd_{short_macd}_{long_macd}_grad'] = add_rolling_average(df, f'macd_{short_macd}_{long_macd}_grad', window_length=60)
df[f'macd_{short_macd}_{long_macd}_grad2'] = add_gradient(df, col=f'macd_{short_macd}_{long_macd}_grad')
df[f'macd_{short_macd}_{long_macd}_grad2'] = df[f'macd_{short_macd}_{long_macd}_grad2']*100
# else:
#     pass

from plots.plots import create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments

create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(df, sticker_name=sticker_csv, indicators=[f'macd_{short_macd}_{long_macd}',
                                                                                                                        f'macd_{short_macd}_{long_macd}_grad',
                                                                                                                        f'macd_{short_macd}_{long_macd}_grad2'])

'''
Stratégia ötlet:
nincsen wathclist, de a néhány órás MACD-t számoljuk, ahol a MACD pozitív, ott a long trendscalping stratégiát használjuk, ahol negatív, ott a short-ot
'''
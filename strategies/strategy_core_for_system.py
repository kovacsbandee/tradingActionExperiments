# TODO meg kell nézni az összes napon a capital és az árgörbe alakulását a kiválasztott, gyakran előforduló sticker-eknél!
# és ebből le kell vezetni a scanner paramétereket!

# TODO: valóban normalizált áron kell megcsinálni a trendscalping-ot! az epsilont ahhoz kell igazítani


import pandas as pd
import os
from joblib import Parallel, delayed
from utils.database_build_driver import get_daywise_common_files
import random
from random import sample
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from analizers.analizers import *

PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = 'F:/tradingActionExperiments_database'

def get_stats_from_results(file_name = 'normalized_strategy_implementation_ind_price_open_epsilon_0_0015.csv',
                            indicator_price = 'open',
                            lower_price_boundary=10,
                            upper_price_boundary = 400,
                            avg_volume_cond = 25000,
                            std_close_lower_boundary_cond = 0.25,
                            epsilon = 0.0015):
    results = pd.read_csv(f'F:/tradingActionExperiments/data_store/{file_name}')
    results = results[(results['volume_max'] != 0)]
    results = results[(~results[f'{indicator_price}_small_normalized_indicator_col_max'].isna())]

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

    # print('Az eredmény file neve: ', file_name)
    # print('Scanner in skewness', skewtest(scanner_in.cap_mean).statistic)
    # print('Scanner out skewness', skewtest(scanner_out.cap_mean).statistic)
    print('in cap mean', scanner_in.cap_mean.mean())
    print('out cap mean', scanner_out.cap_mean.mean())
    print('Azon napok és részvények számának aránya a teljes mintában, amelyeknél 25050-nél nagyobb volt a maximális hoztam', max_winners.shape[0] / results.shape[0])
    print('Azon napok és részvények számának aránya a teljes mintában, amelyeknél 25050-nél nagyobb volt az átlagos hoztam', mean_winners.shape[0] / results.shape[0])
    print('Azon minták, ahol a cap_max nagyobb mint 25050, ott a cap_min is nagyobb!')
    print('Azon napok és részvények számának aránya a teljes mintában, amelyek veszteségesek voltak', losers.shape[0] / results.shape[0])
    return scanner_check, losers, max_winners, mean_winners


def apply_normalized_strategy(place,
                   ma_long=12,
                   ma_short = 5,
                   ind_price = 'open',
                   epsilon = 0.0015,
                   initial_capital = 25000):
    base_data = pd.read_csv(f'{DB_PATH}/daywise_database/{place[0]}/csvs/{place[1]}', index_col='Datetime')
    prev_day_data = pd.read_csv(f'{DB_PATH}/daywise_database/{place[2]}/csvs/{place[1]}', index_col='Datetime')
    pre_market_gap = base_data['open'][0] - prev_day_data['close'][-1]
    sticker_df_cols = ['high', 'low', 'open', 'close', 'volume']
    sticker_df = pd.DataFrame(columns=sticker_df_cols)
    sticker_df.index.name = 'Datetime'

    web_socket_simulator = base_data.iterrows()
    iterator_counter = len(base_data)
    small_ind_col = f'{ind_price}_small_normalized_indicator_col'
    big_ind_col = f'{ind_price}_big_normalized_indicator_col'

    while iterator_counter > 0:
        i, row = next(web_socket_simulator)
        if len(sticker_df) <= ma_long:
            prev_short_in_position_ind = None
            prev_long_in_position_ind = None
            sticker_df.loc[i] = row
            sticker_df.loc[i, f'{ind_price}_norm'] = (sticker_df.loc[i, ind_price] - prev_day_data[ind_price].mean()) / prev_day_data[ind_price].std()
            sticker_df['position'] = 'out'
            sticker_df['trading_action'] = 'no action'
            sticker_df['current_capital'] = initial_capital
            sticker_df['stop_loss_out_signal'] = 'no stop loss signal'
            base_data.drop(index=i, inplace=True)
            iterator_counter -= 1
        else:
            sticker_df.loc[i] = row
            sticker_df.loc[i, f'{ind_price}_norm'] = (sticker_df.loc[i, ind_price] - prev_day_data[ind_price].mean()) / prev_day_data[ind_price].std()

            sticker_df[small_ind_col] = sticker_df[f'{ind_price}_norm'].rolling(ma_short, center=False).mean().diff()
            sticker_df[big_ind_col] = sticker_df[f'{ind_price}_norm'].rolling(ma_long, center=False).mean().diff()

            sticker_df[small_ind_col] = sticker_df[small_ind_col].rolling(ma_short, center=False).mean()
            sticker_df[big_ind_col] = sticker_df[big_ind_col].rolling(ma_long, center=False).mean()

            last_index = sticker_df.index[-1]

            # set position start
            if sticker_df.loc[last_index, small_ind_col] > epsilon and sticker_df.loc[last_index, big_ind_col] > epsilon:
                sticker_df.loc[last_index, 'position'] = 'long_buy'
            elif sticker_df.iloc[-1][small_ind_col] < -epsilon and sticker_df.iloc[-1][big_ind_col] < -epsilon:
                sticker_df.loc[last_index, 'position'] = 'short_sell'
            else:
                sticker_df.loc[last_index, 'position'] = 'out'
            # set position end

            # set trading action
            if sticker_df.iloc[-1]['position'] == sticker_df.iloc[-2]['position']:
                sticker_df.loc[last_index, 'trading_action'] = 'no action'

            if sticker_df.iloc[-1]['position'] == 'long_buy' and sticker_df.iloc[-2]['position'] != 'long_buy':
                sticker_df.loc[last_index, 'trading_action'] = 'buy next long position'
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.iloc[-2]['current_capital']
                prev_long_in_position_ind = last_index

            if sticker_df.iloc[-1]['position'] == 'short_sell' and sticker_df.iloc[-2]['position'] != 'short_sell':
                sticker_df.loc[last_index, 'trading_action'] = 'sell next short position'
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.iloc[-2]['current_capital']
                prev_short_in_position_ind = last_index

            if sticker_df.iloc[-2]['position'] == 'long_buy' and sticker_df.iloc[-1]['position'] != 'long_buy':
                sticker_df.loc[last_index, 'trading_action'] = 'sell previous long position'
                sticker_df.loc[last_index, 'position'] = 'out'

            if sticker_df.iloc[-2]['position'] == 'short_sell' and sticker_df.iloc[-1]['position'] != 'short_sell':
                sticker_df.loc[last_index, 'trading_action'] = 'buy previous short position'
                sticker_df.loc[last_index, 'position'] = 'out'
            # set trading action end

            # calculate capital and apply stop loss start
            if sticker_df.loc[last_index, 'position'] == 'out' and sticker_df.loc[last_index, 'trading_action'] == 'no action':
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.iloc[-2]['current_capital']

            if (sticker_df.loc[last_index, 'position'] == 'long_buy' and sticker_df.loc[last_index, 'trading_action'] == 'no action') or \
                    sticker_df.loc[last_index, 'trading_action'] == 'sell previous long position':
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_long_in_position_ind, 'current_capital'] + \
                                                                (sticker_df.loc[last_index, ind_price] - sticker_df.loc[prev_long_in_position_ind, ind_price]) * \
                                                                (sticker_df.loc[prev_long_in_position_ind, 'current_capital'] / sticker_df.loc[prev_long_in_position_ind, ind_price])

            if (sticker_df.loc[last_index, 'position'] == 'short_sell' and sticker_df.loc[last_index, 'trading_action'] == 'no action') or \
                    sticker_df.loc[last_index, 'trading_action'] == 'buy previous short position':
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_short_in_position_ind, 'current_capital'] + \
                                                                (sticker_df.loc[prev_short_in_position_ind, ind_price] - sticker_df.loc[last_index, ind_price]) * \
                                                                (sticker_df.loc[prev_short_in_position_ind, 'current_capital'] / sticker_df.loc[prev_short_in_position_ind, ind_price])

            if prev_long_in_position_ind is not None:
                if (sticker_df.loc[last_index, ind_price] < sticker_df.loc[prev_long_in_position_ind, ind_price]) and sticker_df.loc[last_index, 'position'] == 'long_buy':
                    sticker_df.loc[last_index, 'stop_loss_out_signal'] = 'stop loss long'
                    sticker_df.loc[last_index, 'trading_action'] = 'sell previous long position'
                    sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_long_in_position_ind, 'current_capital'] + \
                                                                    (sticker_df.loc[last_index, ind_price] - sticker_df.loc[prev_long_in_position_ind, ind_price]) * \
                                                                    (sticker_df.loc[prev_long_in_position_ind, 'current_capital'] /
                                                                     sticker_df.loc[prev_long_in_position_ind, ind_price])
                    sticker_df.loc[last_index, 'position'] = 'out'

            if prev_short_in_position_ind is not None:
                if (sticker_df.loc[last_index, ind_price] > sticker_df.loc[prev_short_in_position_ind, ind_price]) and sticker_df.loc[last_index, 'position'] == 'short_sell':
                    sticker_df.loc[last_index, 'stop_loss_out_signal'] = 'stop loss short'
                    sticker_df.loc[last_index, 'trading_action'] = 'buy previous short position'
                    sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_short_in_position_ind, 'current_capital'] + \
                                                                    (sticker_df.loc[prev_short_in_position_ind, ind_price] - sticker_df.loc[last_index, ind_price]) * \
                                                                    (sticker_df.loc[prev_short_in_position_ind, 'current_capital'] /
                                                                     sticker_df.loc[prev_short_in_position_ind, ind_price])
                    sticker_df.loc[last_index, 'position'] = 'out'
            #calculate capital and apply stop loss end
            iterator_counter -= 1

    sticker_df = \
        pd.merge(base_data,
                 sticker_df[[c for c in sticker_df.columns if c not in sticker_df_cols]],
                 left_index=True,
                 right_index=True,
                 how='left')

    out_file_name = place[1].split('.')[0] + 'w_open_indicators'
    sticker_df.to_csv(f'{DB_PATH}/daywise_database/{place[0]}/csvs/{out_file_name}_normalized_test.csv')
    sticker = sticker_df.copy()
    result_dict = \
        {'sticker': place[1].split('.')[0],
         'sticker_df_len': sticker.shape[0],
         'day': place[0][17:].replace('_', '-'),
         'cap_max': sticker['current_capital'].max(),
         'cap_min': sticker['current_capital'].min(),
         'cap_mean': sticker['current_capital'].mean(),
         f'{ind_price}_max': sticker[ind_price].max(),
         f'{ind_price}_min': sticker[ind_price].min(),
         f'{ind_price}_mean': sticker[ind_price].mean(),
         f'{ind_price}_std': sticker[ind_price].std(),
         f'open_max': sticker['open'].max(),
         f'open_min': sticker['open'].min(),
         f'open_mean': sticker['open'].mean(),
         f'open_std': sticker['open'].std(),
         'high_max': sticker['high'].max(),
         'high_min': sticker['high'].min(),
         'high_std': sticker['high'].std(),
         'low_max': sticker['low'].max(),
         'low_min': sticker['low'].min(),
         'low_std': sticker['low'].std(),
         'price_range_hl': (sticker['high'].max() - sticker['low'].min()) / sticker['close'].mean() * 100,
         'price_range_oc': (sticker['open'].max() - sticker['close'].min()) / sticker['close'].mean() * 100,
         f'volume_max': sticker['volume'].max(),
         f'volume_min': sticker['volume'].min(),
         f'volume_mean': sticker['volume'].mean(),
         'pre_market_gap': pre_market_gap}
    if small_ind_col in sticker.columns:
         result_dict[f'{small_ind_col}_max'] = sticker[small_ind_col].max()
         result_dict[f'{small_ind_col}_min'] = sticker[small_ind_col].min()
         result_dict[f'{small_ind_col}_mean'] = sticker[small_ind_col].mean()
    if big_ind_col in sticker.columns:
        result_dict[f'{big_ind_col}_max'] = sticker[big_ind_col].max()
        result_dict[f'{big_ind_col}_min'] = sticker[big_ind_col].min()
        result_dict[f'{big_ind_col}_mean'] = sticker[big_ind_col].mean()
    return result_dict

place = ('stock_prices_for_2023_11_01', 'DXCM.csv', 'stock_prices_for_2023_10_31')
ind_price = 'open'
ma_long = 12
ma_short = 5
rsi_len = 12
short_macd = 10
long_macd = 22
initial_capital = 25000
epsilon = 0.0015

base_data = pd.read_csv(f'{DB_PATH}/daywise_database/{place[0]}/csvs/{place[1]}', index_col='Datetime')
prev_day_data = pd.read_csv(f'{DB_PATH}/daywise_database/{place[2]}/csvs/{place[1]}', index_col='Datetime')
pre_market_gap = base_data['open'][0] - prev_day_data['close'][-1]
sticker_df_cols = ['high', 'low', 'open', 'close', 'volume']
sticker_df = pd.DataFrame(columns=sticker_df_cols)
sticker_df.index.name = 'Datetime'

base_data['gain_loss'] = base_data['open'].diff(1)
base_data['gain'] = np.where(base_data['gain_loss'] > 0.0, base_data['gain_loss'], 0.0)
base_data['loss'] = -1 * np.where(base_data['gain_loss'] < 0.0, base_data['gain_loss'], 0.0)

base_data['avg_gain'] = base_data['gain'].rolling(rsi_len, center=False).mean()
base_data['avg_loss'] = base_data['loss'].rolling(rsi_len, center=False).mean()
base_data['rsi'] = 100 - (100 / (1 + base_data['avg_gain']/base_data['avg_loss']))

base_data['macd'] = base_data['open'].ewm(span=short_macd, adjust=False, min_periods=short_macd).mean() - base_data['open'].ewm(span=long_macd, adjust=False, min_periods=long_macd).mean()

fig = make_subplots(rows=4, cols=1, shared_xaxes=True)
fig.add_trace(go.Candlestick(x=base_data.index,
                             open=base_data['open'],
                             high=base_data['high'],
                             low=base_data['low'],
                             close=base_data['close'],
                             name=place[1]), row=1, col=1)
fig.add_trace(go.Bar(x=base_data.index,
                     y=base_data['volume'],
                     name='Volume'), row=2, col=1)
fig.add_trace(go.Scatter(x=base_data.index,
                         y=base_data['rsi'],
                         name='rsi',
                         mode='lines',
                         connectgaps=True), row=3, col=1)
fig.add_trace(go.Scatter(x=base_data.index,
                         y=base_data['macd'],
                         name='rsi',
                         mode='lines',
                         connectgaps=True), row=4, col=1)
fig.update_layout(xaxis_rangeslider_visible=False, height=1500)
fig.write_html(f'{PROJ_PATH}/plots/plot_store/normalized_price_data_observations/RSI_test.html')



web_socket_simulator = base_data.iterrows()
iterator_counter = len(base_data)
small_ind_col = f'{ind_price}_small_normalized_indicator_col'
big_ind_col = f'{ind_price}_big_normalized_indicator_col'

while iterator_counter > 0:
    i, row = next(web_socket_simulator)
    if len(sticker_df) <= ma_long:
        prev_short_in_position_ind = None
        prev_long_in_position_ind = None
        sticker_df.loc[i] = row
        sticker_df.loc[i, f'{ind_price}_norm'] = (sticker_df.loc[i, ind_price] - prev_day_data[ind_price].mean()) / prev_day_data[ind_price].std()
        sticker_df['position'] = 'out'
        sticker_df['trading_action'] = 'no action'
        sticker_df['current_capital'] = initial_capital
        sticker_df['stop_loss_out_signal'] = 'no stop loss signal'
        base_data.drop(index=i, inplace=True)
        iterator_counter -= 1
    else:
        sticker_df.loc[i] = row
        sticker_df.loc[i, f'{ind_price}_norm'] = (sticker_df.loc[i, ind_price] - prev_day_data[ind_price].mean()) / prev_day_data[ind_price].std()

        sticker_df[small_ind_col] = sticker_df[f'{ind_price}_norm'].rolling(ma_short, center=False).mean().diff()
        sticker_df[big_ind_col] = sticker_df[f'{ind_price}_norm'].rolling(ma_long, center=False).mean().diff()

        sticker_df[small_ind_col] = sticker_df[small_ind_col].rolling(ma_short, center=False).mean()
        sticker_df[big_ind_col] = sticker_df[big_ind_col].rolling(ma_long, center=False).mean()

        last_index = sticker_df.index[-1]

        # set position start
        if sticker_df.loc[last_index, small_ind_col] > epsilon and sticker_df.loc[last_index, big_ind_col] > epsilon:
            sticker_df.loc[last_index, 'position'] = 'long_buy'
        elif sticker_df.iloc[-1][small_ind_col] < -epsilon and sticker_df.iloc[-1][big_ind_col] < -epsilon:
            sticker_df.loc[last_index, 'position'] = 'short_sell'
        else:
            sticker_df.loc[last_index, 'position'] = 'out'
        # set position end

        # set trading action
        if sticker_df.iloc[-1]['position'] == sticker_df.iloc[-2]['position']:
            sticker_df.loc[last_index, 'trading_action'] = 'no action'

        if sticker_df.iloc[-1]['position'] == 'long_buy' and sticker_df.iloc[-2]['position'] != 'long_buy':
            sticker_df.loc[last_index, 'trading_action'] = 'buy next long position'
            sticker_df.loc[last_index, 'current_capital'] = sticker_df.iloc[-2]['current_capital']
            prev_long_in_position_ind = last_index

        if sticker_df.iloc[-1]['position'] == 'short_sell' and sticker_df.iloc[-2]['position'] != 'short_sell':
            sticker_df.loc[last_index, 'trading_action'] = 'sell next short position'
            sticker_df.loc[last_index, 'current_capital'] = sticker_df.iloc[-2]['current_capital']
            prev_short_in_position_ind = last_index

        if sticker_df.iloc[-2]['position'] == 'long_buy' and sticker_df.iloc[-1]['position'] != 'long_buy':
            sticker_df.loc[last_index, 'trading_action'] = 'sell previous long position'
            sticker_df.loc[last_index, 'position'] = 'out'

        if sticker_df.iloc[-2]['position'] == 'short_sell' and sticker_df.iloc[-1]['position'] != 'short_sell':
            sticker_df.loc[last_index, 'trading_action'] = 'buy previous short position'
            sticker_df.loc[last_index, 'position'] = 'out'
        # set trading action end

        # calculate capital and apply stop loss start
        if sticker_df.loc[last_index, 'position'] == 'out' and sticker_df.loc[last_index, 'trading_action'] == 'no action':
            sticker_df.loc[last_index, 'current_capital'] = sticker_df.iloc[-2]['current_capital']

        if (sticker_df.loc[last_index, 'position'] == 'long_buy' and sticker_df.loc[last_index, 'trading_action'] == 'no action') or \
                sticker_df.loc[last_index, 'trading_action'] == 'sell previous long position':
            sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_long_in_position_ind, 'current_capital'] + \
                                                            (sticker_df.loc[last_index, ind_price] - sticker_df.loc[prev_long_in_position_ind, ind_price]) * \
                                                            (sticker_df.loc[prev_long_in_position_ind, 'current_capital'] / sticker_df.loc[prev_long_in_position_ind, ind_price])

        if (sticker_df.loc[last_index, 'position'] == 'short_sell' and sticker_df.loc[last_index, 'trading_action'] == 'no action') or \
                sticker_df.loc[last_index, 'trading_action'] == 'buy previous short position':
            sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_short_in_position_ind, 'current_capital'] + \
                                                            (sticker_df.loc[prev_short_in_position_ind, ind_price] - sticker_df.loc[last_index, ind_price]) * \
                                                            (sticker_df.loc[prev_short_in_position_ind, 'current_capital'] / sticker_df.loc[prev_short_in_position_ind, ind_price])

        if prev_long_in_position_ind is not None:
            if (sticker_df.loc[last_index, ind_price] < sticker_df.loc[prev_long_in_position_ind, ind_price]) and sticker_df.loc[last_index, 'position'] == 'long_buy':
                sticker_df.loc[last_index, 'stop_loss_out_signal'] = 'stop loss long'
                sticker_df.loc[last_index, 'trading_action'] = 'sell previous long position'
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_long_in_position_ind, 'current_capital'] + \
                                                                (sticker_df.loc[last_index, ind_price] - sticker_df.loc[prev_long_in_position_ind, ind_price]) * \
                                                                (sticker_df.loc[prev_long_in_position_ind, 'current_capital'] /
                                                                 sticker_df.loc[prev_long_in_position_ind, ind_price])
                sticker_df.loc[last_index, 'position'] = 'out'

        if prev_short_in_position_ind is not None:
            if (sticker_df.loc[last_index, ind_price] > sticker_df.loc[prev_short_in_position_ind, ind_price]) and sticker_df.loc[last_index, 'position'] == 'short_sell':
                sticker_df.loc[last_index, 'stop_loss_out_signal'] = 'stop loss short'
                sticker_df.loc[last_index, 'trading_action'] = 'buy previous short position'
                sticker_df.loc[last_index, 'current_capital'] = sticker_df.loc[prev_short_in_position_ind, 'current_capital'] + \
                                                                (sticker_df.loc[prev_short_in_position_ind, ind_price] - sticker_df.loc[last_index, ind_price]) * \
                                                                (sticker_df.loc[prev_short_in_position_ind, 'current_capital'] /
                                                                 sticker_df.loc[prev_short_in_position_ind, ind_price])
                sticker_df.loc[last_index, 'position'] = 'out'
        #calculate capital and apply stop loss end
        iterator_counter -= 1

sticker_df = \
    pd.merge(base_data,
             sticker_df[[c for c in sticker_df.columns if c not in sticker_df_cols]],
             left_index=True,
             right_index=True,
             how='left')

out_file_name = place[1].split('.')[0] + 'w_open_indicators'
sticker_df.to_csv(f'{DB_PATH}/daywise_database/{place[0]}/csvs/{out_file_name}_normalized_test.csv')
sticker = sticker_df.copy()
result_dict = \
    {'sticker': place[1].split('.')[0],
     'sticker_df_len': sticker.shape[0],
     'day': place[0][17:].replace('_', '-'),
     'cap_max': sticker['current_capital'].max(),
     'cap_min': sticker['current_capital'].min(),
     'cap_mean': sticker['current_capital'].mean(),
     f'{ind_price}_max': sticker[ind_price].max(),
     f'{ind_price}_min': sticker[ind_price].min(),
     f'{ind_price}_mean': sticker[ind_price].mean(),
     f'{ind_price}_std': sticker[ind_price].std(),
     f'open_max': sticker['open'].max(),
     f'open_min': sticker['open'].min(),
     f'open_mean': sticker['open'].mean(),
     f'open_std': sticker['open'].std(),
     'high_max': sticker['high'].max(),
     'high_min': sticker['high'].min(),
     'high_std': sticker['high'].std(),
     'low_max': sticker['low'].max(),
     'low_min': sticker['low'].min(),
     'low_std': sticker['low'].std(),
     'price_range_hl': (sticker['high'].max() - sticker['low'].min()) / sticker['close'].mean() * 100,
     'price_range_oc': (sticker['open'].max() - sticker['close'].min()) / sticker['close'].mean() * 100,
     f'volume_max': sticker['volume'].max(),
     f'volume_min': sticker['volume'].min(),
     f'volume_mean': sticker['volume'].mean(),
     'pre_market_gap': pre_market_gap}
if small_ind_col in sticker.columns:
     result_dict[f'{small_ind_col}_max'] = sticker[small_ind_col].max()
     result_dict[f'{small_ind_col}_min'] = sticker[small_ind_col].min()
     result_dict[f'{small_ind_col}_mean'] = sticker[small_ind_col].mean()
if big_ind_col in sticker.columns:
    result_dict[f'{big_ind_col}_max'] = sticker[big_ind_col].max()
    result_dict[f'{big_ind_col}_min'] = sticker[big_ind_col].min()
    result_dict[f'{big_ind_col}_mean'] = sticker[big_ind_col].mean()





# files = get_daywise_common_files(mode='return')
# daily_csvs = list()
# for daily_dict in files:
#     for file in daily_dict['common_files']:
#         daily_csvs.append((daily_dict['day'], file, daily_dict['prev_day']))
#
# sampled_daily_csvs = sample(daily_csvs, 10000)
#
# s = Parallel(n_jobs=16)(delayed(apply_normalized_strategy)(place) for place in daily_csvs)
# results = pd.DataFrame.from_records(s)
# results.to_csv(f'F:/tradingActionExperiments/data_store/normalized_strategy_implementation_ind_price_open_epsilon_0_0015.csv', index=False)


file_open = 'normalized_strategy_implementation_ind_price_open_epsilon_0_0015.csv'

result = pd.read_csv(f'{PROJ_PATH}/data_store/{file_open}')
result = result[(~result.cap_max.isna())].copy()
result = result[(~result.open_big_normalized_indicator_col_mean.isna())].copy()
result['traded_volume'] = result['open_mean']*result['volume_mean']
result = result[result['traded_volume'] > 150000].copy()

time_series = result.pivot_table(columns=['day'], index=['sticker'], values=['cap_mean', 'cap_max', 'open_std', 'volume_mean', 'open_max', 'price_range_hl', 'pre_market_gap', 'open_small_normalized_indicator_col_max'])

ts = result.pivot_table(columns=['day'], index=['sticker'], values=['cap_max'])

ts = ts[ts.index.isin(ts[ts.isna().sum(axis=1)==0].index)]

ts_trans = ts.T.copy()

l = list()
for c in ts_trans.columns:
    l.append((c, ts_trans[c].autocorr()))
    print(c, ts_trans[c].autocorr())

datafram = pd.DataFrame.from_records(l, columns=['sticker', 'autocorr'])

datafram.sort_values(by='autocorr', inplace=True)

corr_df=\
result[['traded_volume','cap_max', 'cap_min', 'cap_mean', 'open_max',
       'open_min', 'open_mean', 'open_std', 'high_max', 'high_min', 'high_std',
       'low_max', 'low_min', 'low_std', 'price_range_hl', 'price_range_oc',
       'volume_max', 'volume_min', 'volume_mean', 'pre_market_gap',
       'open_small_normalized_indicator_col_max',
       'open_small_normalized_indicator_col_min',
       'open_small_normalized_indicator_col_mean',
       'open_big_normalized_indicator_col_max',
       'open_big_normalized_indicator_col_min',
       'open_big_normalized_indicator_col_mean']].corr()




open_results, open_losers, open_max_winners, open_mean_winners = get_stats_from_results(file_name=file_open, indicator_price='open')

open_losers['traded_value'] = open_losers['open_mean']*open_losers['volume_mean']


losers = open_losers[open_losers.cap_mean < 24000]
compare_results(loser_df=losers, winners_df=open_mean_winners, indicator_price='open', plot_name=f'{file_open}_mean')


compare_results(loser_df=open_losers, winners_df=open_max_winners, indicator_price='open', plot_name=f'{file_open}_max')





open_mean_tpg = analyse_in_respect_of_total_period(w_or_l_df = open_mean_winners,
                                                   res_df = open_results,
                                                   occ_freq  = 14)


# for eps in [0.1, 0.01, 0.001, 0.0001, 0.00001]:
#     file_open = f'normalized_strategy_implementation_ind_price_open_epsilon_{eps}.csv'
#     print(file_open)
#     print(eps)
#     df = pd.read_csv(f'F:/tradingActionExperiments/data_store/{file_open}')
#     # print(df.groupby(by='sticker').agg({'cap_max': 'mean',
#     #                                     'cap_min': 'mean',
#     #                                     'cap_mean': 'mean'}))
#     print(df['cap_max'].mean(), df['cap_min'].mean(), df['cap_mean'].mean())
#
#
#     open_results, open_losers, open_max_winners, open_mean_winners = get_stats_from_results(file_name=file_open,
#                                                                                             indicator_price='open')
#     compare_results(loser_df=open_losers, winners_df=open_mean_winners, indicator_price='open',
#                     plot_name=f'{file_open}_mean')
#     compare_results(loser_df=open_losers, winners_df=open_max_winners, indicator_price='open',
#                     plot_name=f'{file_open}_max')
#     open_mean_tpg = analyse_in_respect_of_total_period(w_or_l_df=open_mean_winners,
#                                                        res_df=open_results,
#                                                        occ_freq=14)
#
#     sample_csvs = sample(daily_csvs, 10)
#     sample_csvs = [list(t) for t in sample_csvs]
#     for l in sample_csvs:
#         l.append(eps)
#     s = Parallel(n_jobs=16)(delayed(apply_normalized_strategy)(place) for place in sample_csvs)
#     results = pd.DataFrame.from_records(s)
#     results.to_csv(f'F:/tradingActionExperiments/data_store/normalized_strategy_implementation_ind_price_open_epsilon_{eps}.csv', index=False)
#     print(eps, sample_csvs)


def general_candlestick_chart(sticker_day_df, epsilon=0.0015, plot_name=''):
    for i, row in sticker_day_df.iterrows():
        date = row['day'].replace('-', '_')
        sticker = row['sticker']
        sticker_df = pd.read_csv(f'{DB_PATH}/daywise_database/stock_prices_for_{date}/csvs/{sticker}w_open_indicators_normalized_test.csv', index_col='Datetime')
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True)
        fig.add_trace(go.Candlestick(x=sticker_df.index,
                                     open=sticker_df['open'],
                                     high=sticker_df['high'],
                                     low=sticker_df['low'],
                                     close=sticker_df['close'],
                                     name=sticker), row=1, col=1)
        fig.add_trace(go.Bar(x=sticker_df.index,
                             y=sticker_df['volume'],
                             name='Volume'), row=2, col=1)
        fig.add_trace(go.Scatter(x=sticker_df.index,
                                 y=sticker_df['current_capital'],
                                 name='current_capital',
                                 mode='lines',
                                 connectgaps=True), row=3, col=1)
        fig.add_trace(go.Scatter(x=sticker_df.index,
                                 y=sticker_df['open_small_normalized_indicator_col'],
                                 name='open_small_normalized_indicator_col',
                                 mode='lines',
                                 connectgaps=True), row=4, col=1)
        fig.add_hline(-epsilon,line_width=1, row=4, col=1)
        fig.add_hline(epsilon, line_width=1, row=4, col=1)
        fig.add_trace(go.Scatter(x=sticker_df.index,
                                 y=sticker_df['open_big_normalized_indicator_col'],
                                 name='open_big_normalized_indicator_col',
                                 mode='lines',
                                 connectgaps=True), row=5, col=1)
        fig.add_hline(-epsilon, line_width=1, row=5, col=1)
        fig.add_hline(epsilon, line_width=1, row=5, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False,height=1500)
        fig.write_html(f'{PROJ_PATH}/plots/plot_store/normalized_price_data_observations/normalized_price_observations_for_{sticker}_day_{date}_{plot_name}.html')

losers['traded_value'] = losers['open_mean']*losers['volume_mean']

open_mean_winners['traded_value'] = open_mean_winners['open_mean'] * open_mean_winners['volume_mean']

random.seed(11)
general_candlestick_chart(sticker_day_df = losers.sample(20)[['sticker', 'day']], plot_name='losers')

open_mean_winners = open_mean_winners[open_mean_winners.traded_value > 5*25000].copy()

open_mean_winners.sort_values(by='cap_mean', inplace=True)
general_candlestick_chart(sticker_day_df = open_mean_winners[['sticker', 'day']][0:10], plot_name='mean_winners_eleje')
general_candlestick_chart(sticker_day_df = open_mean_winners[['sticker', 'day']][-10:], plot_name='mean_winners_vege')

general_candlestick_chart(sticker_day_df = open_mean_winners.sample(10)[['sticker', 'day']], plot_name='mean_winners_random')


result_sort_byPrice_range = result.sort_values(by=['cap_mean','traded_volume', 'price_range_hl'])[['sticker', 'day', 'traded_volume', 'cap_mean', 'cap_max', 'price_range_hl']]
d = result_sort_byPrice_range[result_sort_byPrice_range.traded_volume>250000]
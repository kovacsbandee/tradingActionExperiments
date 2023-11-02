import pandas as pd
import numpy as np
import os
from joblib import Parallel, delayed
import plotly.graph_objects as go
from plotly.subplots import make_subplots



PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = 'F:/tradingActionExperiments_database'

results = pd.read_csv(f'F:/tradingActionExperiments/data_store/final_strategy_implementation_results_on_daily_w_price_ranges.csv')
results = results[(results['volume_max'] != 0)]
results = results[(~results['close_small_ind_col_max'].isna())]


max_winners = results[results['cap_max'] > 25050]
mean_winners = results[results['cap_mean'] > 25050]

losers = results[results['cap_max'] == 25000]
print('Azon napok és részvények számának aránya a teljes mintában, amelyeknél 25050-nél nagyobb volt a maximális hoztam', max_winners.shape[0]/results.shape[0])
print('Azon napok és részvények számának aránya a teljes mintában, amelyeknél 25050-nél nagyobb volt az átlagos hoztam', mean_winners.shape[0]/results.shape[0])
print('Azon minták, ahol a cap_max nagyobb mint 25050, ott a cap_min is nagyobb!')
print('Azon napok és részvények számának aránya a teljes mintában, amelyek veszteségesek voltak', losers.shape[0]/results.shape[0])


# össze kell hasonlítani a mean_winnerst és a loserts!


# vars = ['cap_max', 'cap_min', 'cap_mean', 'close_max', 'close_min', 'close_mean', 'volume_max', 'volume_min', 'volume_mean',
#         'close_small_ind_col_max', 'close_small_ind_col_min', 'close_small_ind_col_mean', 'close_big_ind_col_max',
#         'close_big_ind_col_min', 'close_big_ind_col_mean']

vars = ['cap_max', 'cap_min', 'cap_mean', 'close_max',
       'close_min', 'close_mean', 'close_std', 'open_max', 'open_min',
       'open_mean', 'open_std', 'high_max', 'high_min', 'high_std', 'low_max',
       'low_min', 'low_std', 'price_range_hl', 'price_range_oc', 'volume_max',
       'volume_min', 'volume_mean', 'close_small_ind_col_max',
       'close_small_ind_col_min', 'close_small_ind_col_mean',
       'close_big_ind_col_max', 'close_big_ind_col_min',
       'close_big_ind_col_mean']

fig = make_subplots(cols=1,
                    subplot_titles=vars,
                    rows=len(vars))

for i, v in enumerate(vars):
    fig.add_trace(go.Histogram(x=losers[v],
                               name='losers',
                               nbinsx=100,
                               showlegend=True if i == 0 else False,
                               histnorm='probability',
                               marker = dict(color='blue')), col=1, row=i + 1)
    fig.add_trace(go.Histogram(x=mean_winners[v],
                               name='mean_winners',
                               nbinsx=100,
                               showlegend=True if i==0 else False,
                               histnorm='probability',
                               marker = dict(color='red')), col=1, row=i + 1)
fig.update_layout(barmode='overlay',
                  height=len(vars)*150)
fig.update_traces(opacity=0.5)
fig.write_html(f'{PROJ_PATH}/plots/plot_store/losers_and_mean_winner_comparision.html')


mean_winners.to_csv(f'F:/tradingActionExperiments/data_store/mean_winners_final_strategy_implementation_results_on_daily.csv', index=False)
losers.to_csv(f'F:/tradingActionExperiments/data_store/losers_final_strategy_implementation_results_on_daily.csv', index=False)


occurance_freq = mean_winners.groupby(by='sticker').count().sort_values(by='day', ascending=False).reset_index()
occurance_freq = occurance_freq[['sticker', 'day']]
occurance_freq.columns = ['sticker', 'occurance_freq']
mean_winners = pd.merge(mean_winners, occurance_freq, how='left', on='sticker')

df = pd.merge(results, occurance_freq, how='right', on='sticker')
df = df[df.occurance_freq > 12].sort_values(by=['sticker', 'day'])
df = pd.merge(df,
              df[['sticker', 'cap_min', 'cap_mean', 'cap_max']].groupby(by=['sticker']).mean().rename({'cap_min': 'cap_min_avg',
                                                                                                       'cap_mean': 'cap_mean_avg',
                                                                                                       'cap_max': 'cap_max_avg'}, axis='columns').reset_index(),
              how='left',
              on='sticker')
df = df[['sticker', 'day', 'cap_max', 'cap_min', 'cap_mean', 'cap_min_avg', 'cap_mean_avg', 'cap_max_avg']]
df['daily_gain'] = df['cap_max']-25000
tdf = df[['sticker', 'daily_gain']].groupby(by='sticker').sum()
print(tdf)
avg_gain = df[~df['sticker'].isin(['AMAM', 'ZJYL'])][['sticker', 'daily_gain']].groupby(by='sticker').sum().mean()
print(avg_gain/25000)
print(np.power(1+avg_gain/25000, 12))

test = mean_winners[mean_winners.occurance_freq > 16]
test.sort_values(by=['sticker', 'day'], inplace=True)
plot = results[results.sticker.isin(list(test.sticker.unique()))]
ts_variables = ['cap_max', 'cap_min', 'cap_mean', 'close_small_ind_col_mean', 'close_big_ind_col_mean']
plot.set_index('day', inplace=True)
days = plot.index.unique()

fig = make_subplots(rows=len(days),
                    cols=len(ts_variables),
#                    row_titles=days,
                    subplot_titles=ts_variables)


for j, d in enumerate(days):
    daily_plot = plot[plot.index == d]
    for i, col in enumerate(ts_variables):
        fig.add_trace(go.Histogram(x=daily_plot[col],
                                   name=d,
                                   showlegend=True if i==0 else False), row=j + 1, col=i + 1)
fig.update_layout(height=len(vars) * 150)
fig.write_html(f'{PROJ_PATH}/plots/plot_store/profitability_in_time.html')


df = pd.merge(results, occurance_freq, how='right', on='sticker')
df = df[df.occurance_freq > 17].sort_values(by=['sticker', 'day'])
df = pd.merge(df,
              df[['sticker', 'cap_min', 'cap_mean', 'cap_max']].groupby(by=['sticker']).mean().rename({'cap_min': 'cap_min_avg',
                                                                                                       'cap_mean': 'cap_mean_avg',
                                                                                                       'cap_max': 'cap_max_avg'}, axis='columns').reset_index(),
              how='left',
              on='sticker')
df = df[['sticker', 'day', 'cap_max', 'cap_min', 'cap_mean', 'cap_min_avg', 'cap_mean_avg', 'cap_max_avg']]

# TODO meg kell nézni az összes napon a capital és az árgörbe alakulását a kiválasztott, gyakran előforduló sticker-eknél!
# és ebből le kell vezetni a scanner paramétereket!
# TODO: valóban normalizált áron kell megcsinálni a trendscalping-ot! az epsilont ahhoz kell igazítani



daily_csvs = list()
for day_dir in os.listdir(f'{DB_PATH}/daywise_database'):
    for file in os.listdir(f'{DB_PATH}/daywise_database/{day_dir}/csvs'):
        daily_csvs.append((day_dir, file))


def apply_strategy(place,
                   ma_long=12,
                   ma_short = 5,
                   ind_price = 'close',
                   epsilon = 0.01,
                   initial_capital = 25000):
    base_data = pd.read_csv(f'{DB_PATH}/daywise_database/{place[0]}/csvs/{place[1]}', index_col='Datetime')

    sticker_df = pd.DataFrame(columns=['high', 'low', 'open', 'close', 'volume'])
    sticker_df.index.name = 'Datetime'

    web_socket_simulator = base_data.iterrows()
    iterator_counter = len(base_data)
    small_ind_col = f'{ind_price}_small_ind_col'
    big_ind_col = f'{ind_price}_big_ind_col'
    while iterator_counter > 0:
        i, row = next(web_socket_simulator)
        if len(sticker_df) <= ma_long:
            prev_short_in_position_ind = None
            prev_long_in_position_ind = None
            sticker_df.loc[i] = row
            sticker_df['position'] = 'out'
            sticker_df['trading_action'] = 'no action'
            sticker_df['current_capital'] = initial_capital
            sticker_df['stop_loss_out_signal'] = 'no stop loss signal'
            base_data.drop(index=i, inplace=True)
            iterator_counter -= 1
        else:
            sticker_df.loc[i] = row
            sticker_df[small_ind_col] = sticker_df[ind_price].rolling(ma_short, center=False).mean().diff()
            sticker_df[big_ind_col] = sticker_df[ind_price].rolling(ma_long, center=False).mean().diff()
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

    out_file_name = place[1].split('.')[0] + 'sdf.csv'
    sticker_df.to_csv(f'{DB_PATH}/daywise_database/{place[0]}/csvs/{out_file_name}_sdf.csv')

    result_dict = \
    {'sticker': place[1].split('.')[0],
     'day': place[0][17:].replace('_', '-'),
     'cap_max': sticker_df['current_capital'].max(),
     'cap_min': sticker_df['current_capital'].min(),
     'cap_mean': sticker_df['current_capital'].mean(),
     f'{ind_price}_max': sticker_df[ind_price].max(),
     f'{ind_price}_min': sticker_df[ind_price].min(),
     f'{ind_price}_mean': sticker_df[ind_price].mean(),
     f'{ind_price}_std': sticker_df[ind_price].std(),
     f'open_max': sticker_df['open'].max(),
     f'open_min': sticker_df['open'].min(),
     f'open_mean': sticker_df['open'].mean(),
     f'open_std': sticker_df['open'].std(),
     'high_max': sticker_df['high'].max(),
     'high_min': sticker_df['high'].min(),
     'high_std': sticker_df['high'].std(),
     'low_max': sticker_df['low'].max(),
     'low_min': sticker_df['low'].min(),
     'low_std': sticker_df['low'].std(),
     'price_range_hl': (sticker_df['high'].max() - sticker_df['low'].min()) / sticker_df['close'].mean() * 100,
     'price_range_oc': (sticker_df['open'].max() - sticker_df['close'].min()) / sticker_df['close'].mean() * 100,
     f'volume_max': sticker_df['volume'].max(),
     f'volume_min': sticker_df['volume'].min(),
     f'volume_mean': sticker_df['volume'].mean()}

    if small_ind_col in sticker_df.columns:
         result_dict[f'{small_ind_col}_max'] = sticker_df[small_ind_col].max()
         result_dict[f'{small_ind_col}_min'] = sticker_df[small_ind_col].min()
         result_dict[f'{small_ind_col}_mean'] = sticker_df[small_ind_col].mean()
    if big_ind_col in sticker_df.columns:
        result_dict[f'{big_ind_col}_max'] = sticker_df[big_ind_col].max()
        result_dict[f'{big_ind_col}_min'] = sticker_df[big_ind_col].min()
        result_dict[f'{big_ind_col}_mean'] = sticker_df[big_ind_col].mean()
    return result_dict

s = Parallel(n_jobs=16)(delayed(apply_strategy)(place) for place in daily_csvs)
results = pd.DataFrame.from_records(s)
results.to_csv(f'F:/tradingActionExperiments/data_store/final_strategy_implementation_results_on_daily_w_price_ranges.csv', index=False)


import pandas as pd
import os
from joblib import Parallel, delayed
DB_PATH = 'F:/tradingActionExperiments_database'

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

    sticker_df = pd.DataFrame(columns=['high', 'low', 'close', 'volume'])
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

    result_dict = \
    {'sticker': place[1].split('.')[0],
     'day': place[0][17:].replace('_', '-'),
     'cap_max': sticker_df['current_capital'].max(),
     'cap_min': sticker_df['current_capital'].min(),
     'cap_mean': sticker_df['current_capital'].mean(),
     f'{ind_price}_max': sticker_df[ind_price].max(),
     f'{ind_price}_min': sticker_df[ind_price].min(),
     f'{ind_price}_mean': sticker_df[ind_price].mean(),
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
results.to_csv(f'F:/tradingActionExperiments/data_store/final_strategy_implementation_results_on_daily.csv', index=False)


import pandas as pd
from datetime import datetime, timedelta
from data_sources.add_indicators import add_gradient, add_rolling_average


PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = f'F:/tradingActionExperiments_database'


def add_trendscalping_specific_indicators(df,
                                          averaged_cols=['close'],
                                          ma_short=5,
                                          ma_long=12):
    for col in averaged_cols:
        short_ind_col = f'{col}_ma{ma_short}'
        df[short_ind_col] = add_rolling_average(price_time_series=df,
                                                col=col,
                                                window_length=ma_short)
        df[f'{short_ind_col}_grad'] = add_gradient(price_time_series=df,
                                                   col=short_ind_col)
        long_ind_col = f'{col}_ma{ma_long}'
        df[long_ind_col] = add_rolling_average(price_time_series=df,
                                               col=col,
                                               window_length=ma_long)
        df[f'{long_ind_col}_grad'] = add_gradient(price_time_series=df,
                                                  col=long_ind_col)
        return df


def create_strategy_filter(df, ind_price, ma_short, ma_long, short_epsilon = 0.01, long_epsilon = 0.01):
    # reutrns a boolean filter sequence for long buy, and another one for short sell
    short_grad = f'{ind_price}_ma{ma_short}_grad'
    long_grad = f'{ind_price}_ma{ma_long}_grad'

    long_filter = (long_epsilon < df[long_grad]) & (short_epsilon < df[short_grad])
    short_filter = (-long_epsilon > df[long_grad]) & (-short_epsilon > df[short_grad])
    return {'short_filter': short_filter, 'long_filter': long_filter}


def apply_strategy_w_stop_loss(df,
                               filters,
                               ind_price = 'open',
                               stopping_crit_hour = None,
                               initial_capital = 3000,
                               comission_ratio = 0.0,
                               stop_loss_perc = 0.0):
    # if stopping_crit_hour is not None:
    #     df = df[df.index < df.index[0].split(' ')[0] + f' {stopping_crit_hour}:00:00-04:00'].copy()
    df['position'] = 'out'
    # add positions
    df.loc[filters['long_filter'].values, 'position'] = 'long_buy'
    df.loc[filters['short_filter'].values, 'position'] = 'short_sell'
    df['trading_action'] = ''
    df['prev_position_lagged'] = df['position'].shift(1)

    # init prev indices
    prev_capital_indices = list()
    if 'long_buy' in df['position'].unique():
        prev_long_buy_position_index = df[df['position'] == 'long_buy'].index[0]
        prev_capital_indices.append(prev_long_buy_position_index)

    if 'short_sell' in df['position'].unique():
        prev_short_sell_position_index = df[df['position'] == 'short_sell'].index[0]
        prev_capital_indices.append(prev_short_sell_position_index)

    df['gain_per_position'] = 0
    df['current_capital'] = 0
    prev_capital_index = min(prev_capital_indices) if len(prev_capital_indices)>0 else df.index[0]
    df.loc[prev_capital_index, 'current_capital'] = initial_capital

    tz_str = df.index[0][-6:]

    for i, row in df.iterrows():
        # ha a mostani capital rosszabb mint az i-edik sorban a price add el, és update-elj minden indexet!
        # különben mehet tovább lefelé!
        current_last_in_position_indices = []
        try:
            current_last_in_position_indices.append(prev_long_buy_position_index)
        except:
            pass
        try:
            current_last_in_position_indices.append(prev_short_sell_position_index)
        except:
            pass
        current_last_in_position_index = max(current_last_in_position_indices) if len(current_last_in_position_indices)>0 else df.index[0]
        if row['current_capital'] - stop_loss_perc * df.loc[current_last_in_position_index, 'current_capital'] < 0:
            # add el:
            if current_last_in_position_index == prev_long_buy_position_index:
                #prev_short_sell_position_index = i
                df.loc[i, 'gain_per_position'] = df.loc[i, ind_price] - df.loc[prev_long_buy_position_index, ind_price]
                df.loc[i, 'current_capital'] = (df.loc[prev_capital_index, 'current_capital'] + \
                                                (df.loc[i, 'gain_per_position'] * \
                                                 (df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                  df.loc[prev_long_buy_position_index, ind_price]))) - \
                                               comission_ratio * df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
                forward_t_ind = i
                while df.loc[forward_t_ind, 'position'] == 'long_buy':
                    df.loc[forward_t_ind, 'position'] = 'out'
                    df.loc[forward_t_ind, 'prev_position_lagged'] = 'out'
                    forward_t_ind = str(datetime.strptime(df.index[0][:-6], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)) + tz_str
            if current_last_in_position_index == prev_short_sell_position_index:
                df.loc[i, 'gain_per_position'] = df.loc[prev_short_sell_position_index, ind_price] - df.loc[i, ind_price]
                df.loc[i, 'current_capital'] = (df.loc[prev_capital_index, 'current_capital'] + \
                                                (df.loc[i, 'gain_per_position'] * \
                                                 (df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                  df.loc[prev_short_sell_position_index, ind_price]))) - \
                                               comission_ratio * df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
                forward_t_ind = i
                while df.loc[forward_t_ind, 'position'] == 'long_buy':
                    df.loc[forward_t_ind, 'position'] = 'out'
                    df.loc[forward_t_ind, 'prev_position_lagged'] = 'out'
                    forward_t_ind = str(
                        datetime.strptime(df.index[0][:-6], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)) + tz_str
        else:
            # buy long position eset
            if row['prev_position_lagged'] == 'out' and row['position'] == 'long_buy':
                prev_long_buy_position_index = i
                df.loc[i, 'current_capital'] = df.loc[prev_capital_index, 'current_capital']
            # sell short eset
            if row['prev_position_lagged'] == 'out' and row['position'] == 'short_sell':
                prev_short_sell_position_index = i
                df.loc[i, 'current_capital'] = df.loc[prev_capital_index, 'current_capital']
            # sell long eset
            if row['prev_position_lagged'] == 'long_buy' and row['position'] == 'out':
                df.loc[i, 'gain_per_position'] = df.loc[i, ind_price] - df.loc[prev_long_buy_position_index, ind_price]
                df.loc[i, 'current_capital'] = (df.loc[prev_capital_index, 'current_capital'] + \
                                                (df.loc[i, 'gain_per_position'] * \
                                                 (df.loc[prev_long_buy_position_index, 'current_capital'] / \
                                                  df.loc[prev_long_buy_position_index, ind_price]))) - \
                                               comission_ratio * df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            # buy short eset
            if row['prev_position_lagged'] == 'short_sell' and row['position'] == 'out':
                df.loc[i, 'gain_per_position'] = df.loc[prev_short_sell_position_index, ind_price] - df.loc[i, ind_price]
                df.loc[i, 'current_capital'] = (df.loc[prev_capital_index, 'current_capital'] + \
                                                (df.loc[i, 'gain_per_position'] * \
                                                (df.loc[prev_short_sell_position_index, 'current_capital'] / \
                                                 df.loc[prev_short_sell_position_index, ind_price]))) - \
                                               comission_ratio * df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            # buy short-sell long eset
            if row['prev_position_lagged'] == 'short_sell' and row['position'] == 'long_buy':
                prev_long_buy_position_index = i
                df.loc[i, 'gain_per_position'] = df.loc[prev_short_sell_position_index, ind_price] - df.loc[i, ind_price]
                df.loc[i, 'current_capital'] = (df.loc[prev_capital_index, 'current_capital'] + \
                                                (df.loc[i, 'gain_per_position'] * \
                                                (df.loc[prev_short_sell_position_index, 'current_capital'] / \
                                                 df.loc[prev_short_sell_position_index, ind_price]))) - \
                                               comission_ratio * df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            # sell long  - buy short eset
            if row['prev_position_lagged'] == 'long_buy' and row['position'] == 'short_sell':
                prev_short_sell_position_index = i
                df.loc[i, 'gain_per_position'] = df.loc[i, ind_price] - df.loc[prev_long_buy_position_index, ind_price]
                df.loc[i, 'current_capital'] = (df.loc[prev_capital_index, 'current_capital'] + \
                                                (df.loc[i, 'gain_per_position'] * \
                                                (df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                 df.loc[prev_long_buy_position_index, ind_price]))) - \
                                               comission_ratio * df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
    return df
#
# sticker = 'AAPL'
# sticker_csv = f'{sticker}.csv'
# df = pd.read_csv(f'{DB_PATH}/stockwise_database/{sticker_csv}', index_col='Datetime')
#
# ma_short=5
# ma_long=12
# ind_price = 'close'
#
# indicators = ['close_ma5', 'close_ma5_grad', 'close_ma12', 'close_ma12_grad']
#
#
# df = add_trendscalping_specific_indicators(df, averaged_cols=[ind_price], ma_short=ma_short, ma_long=ma_long)
# filts = create_strategy_filter(ind_price=ind_price)
#
# df = apply_strategy_w_stop_loss(df, filters=filts)
#

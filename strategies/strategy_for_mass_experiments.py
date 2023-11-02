import pandas as pd
from datetime import datetime, timedelta
from data_sources.add_indicators import add_gradient, add_rolling_average, add_MACD

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

def apply_simple_combined_trendscalping_for_mass(df,
                                                 ind_price='close',
                                                 stopping_crit_hour = None,
                                                 ma_short=5,
                                                 ma_long=12,
                                                 short_epsilon = 0.01,
                                                 long_epsilon = 0.01,
                                                 initial_capital=3000,
                                                 comission_ratio=0.0):

    if stopping_crit_hour is not None:
        df = df[df.index < df.index[0].split(' ')[0]+f' {stopping_crit_hour}:00:00-04:00'].copy()
    df['position'] = 'out'
    df.loc[
        (long_epsilon < df[f'{ind_price}_ma{ma_long}_grad']) & (short_epsilon < df[f'{ind_price}_ma{ma_short}_grad']),
        'position'] = 'long_buy'
    df.loc[
        (-long_epsilon > df[f'{ind_price}_ma{ma_long}_grad']) & (-short_epsilon > df[f'{ind_price}_ma{ma_short}_grad']),
        'position'] = 'short_sell'
    df['trading_action'] = ''
    df['prev_position_lagged'] = df['position'].shift(1)

    df.loc[(df['prev_position_lagged'] == 'out') & (df['position'] == 'long_buy'),
           'trading_action'] = 'buy next long position'

    df.loc[((df['prev_position_lagged'] == 'long_buy') & (df['position'] == 'out') ),
           'trading_action'] = 'sell previous long position'

    df.loc[(df['prev_position_lagged'] == 'out') & (df['position'] == 'short_sell'),
           'trading_action'] = 'sell next short position'

    df.loc[((df['prev_position_lagged'] == 'short_sell') & (df['position'] == 'out')),
           'trading_action'] = 'buy previous short position'

    df.loc[(df['prev_position_lagged'] == 'short_sell') & (df['position'] == 'long_buy'),
           'trading_action'] = 'buy previous short position and buy next long position'

    df.loc[(df['prev_position_lagged'] == 'long_buy') & (df['position'] == 'short_sell'),
           'trading_action'] = 'sell previous long position and sell next short position'
    last_indices = list()
    sell_longs = df[df['trading_action'] == 'sell previous long position'].index
    if len(sell_longs)>0:
        last_indices.append(sell_longs[-1])
    buy_shorts = df[df['trading_action'] == 'buy previous short position'].index
    if len(buy_shorts)>0:
        last_indices.append(buy_shorts[-1])
    if len(last_indices)>0:
        df.loc[df.index > max(last_indices), 'trading_action'] = ''
    trading_action_df = df[df['trading_action'] != ''].copy()

    if trading_action_df.shape[0] > 0:
        trading_action_df['gain_per_position'] = 0
        prev_capital_indices = list()
        if 'sell next short position' in trading_action_df['trading_action'].unique():
            prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'sell next short position'].index[0]
            prev_capital_indices.append(prev_short_sell_position_index)
        if 'buy next long position' in trading_action_df['trading_action'].unique():
            prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
            prev_capital_indices.append(prev_long_buy_position_index)
        prev_capital_index = min(prev_capital_indices)
        trading_action_df['current_capital'] = 0
        trading_action_df.loc[prev_capital_index, 'current_capital'] = initial_capital
        for i, row in trading_action_df.iterrows():
            if row['trading_action'] == 'buy next long position':
                prev_long_buy_position_index = i
                trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
            if row['trading_action'] == 'sell next short position':
                prev_short_sell_position_index = i
                trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
            if row['trading_action'] == 'buy previous short position and buy next long position':
                prev_long_buy_position_index = i
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, ind_price] - trading_action_df.loc[i, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                               trading_action_df.loc[prev_short_sell_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            if row['trading_action'] == 'sell previous long position and sell next short position':
                prev_short_sell_position_index = i
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, ind_price] - trading_action_df.loc[prev_long_buy_position_index, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                               trading_action_df.loc[prev_long_buy_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            if row['trading_action'] == 'sell previous long position':
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, ind_price] - trading_action_df.loc[prev_long_buy_position_index, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                              trading_action_df.loc[prev_long_buy_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            if row['trading_action'] == 'buy previous short position':
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, ind_price] - trading_action_df.loc[i, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                               trading_action_df.loc[prev_short_sell_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
        if trading_action_df is not None:
            df = pd.merge(df,
                          trading_action_df[['gain_per_position', 'current_capital', 'trading_action']],
                          how='left',
                          left_index=True,
                          right_index=True)
            df['gain_per_position'].fillna(0.0, inplace=True)
            df['current_capital'].fillna(0.0, inplace=True)
            return df
    else:
        df['gain_per_position'] = 0.0
        df['current_capital'] = 0.0
        df['trading_action'] = ''
        return df



def add_macd_and_trendscalping_indicators(df,
                                          averaged_cols=['open'],
                                          ma_tscalp_short=5,
                                          ma_tscalp_long=12,
                                          short_macd=100,
                                          long_macd=220):
        for col in averaged_cols:
            df[f'macd_{short_macd}_{long_macd}'] = add_MACD(df, col=col, short_macd=short_macd, long_macd=long_macd)
            df[f'macd_{short_macd}_{long_macd}_grad'] = add_gradient(df, col=f'macd_{short_macd}_{long_macd}')
            df[f'macd_{short_macd}_{long_macd}_grad_ma'] = add_rolling_average(df,
                                                                               f'macd_{short_macd}_{long_macd}_grad',
                                                                               window_length=60)
            df.loc[df[f'macd_{short_macd}_{long_macd}_grad_ma'] < 0, 'long_short_sign'] = -1
            df.loc[df[f'macd_{short_macd}_{long_macd}_grad_ma'] > 0, 'long_short_sign'] = 1

            short_ind_col = f'{col}_ma{ma_tscalp_short}'
            df[short_ind_col] = add_rolling_average(price_time_series=df,
                                                            col=col,
                                                            window_length=ma_tscalp_short)
            df[f'{short_ind_col}_grad'] = add_gradient(price_time_series=df,
                                                               col=short_ind_col)
            long_ind_col = f'{col}_ma{ma_tscalp_long}'
            df[long_ind_col] = add_rolling_average(price_time_series=df,
                                                           col=col,
                                                           window_length=ma_tscalp_long)
            df[f'{long_ind_col}_grad'] = add_gradient(price_time_series=df,
                                                              col=long_ind_col)
        return df

def apply_macd_enhanced_trendscalping(df,
                                      ind_price='open',
                                      stopping_crit_hour = None,
                                      ma_short=5,
                                      ma_long=12,
                                      short_epsilon = 0.01,
                                      long_epsilon = 0.01,
                                      initial_capital=3000,
                                      comission_ratio=0.0):
    if stopping_crit_hour is not None:
        df = df[df.index < df.index[0].split(' ')[0]+f' {stopping_crit_hour}:00:00-04:00'].copy()
    df['position'] = 'out'
    df.loc[
        (0.0 < df['long_short_sign']) &
        (long_epsilon < df[f'{ind_price}_ma{ma_long}_grad']) & (short_epsilon < df[f'{ind_price}_ma{ma_short}_grad']),
        'position'] = 'long_buy'
    df.loc[
        (df['long_short_sign'] < 0.0) &
        (-long_epsilon > df[f'{ind_price}_ma{ma_long}_grad']) & (-short_epsilon > df[f'{ind_price}_ma{ma_short}_grad']),
        'position'] = 'short_sell'
    df['trading_action'] = ''
    df['prev_position_lagged'] = df['position'].shift(1)

    df.loc[(df['prev_position_lagged'] == 'out') & (df['position'] == 'long_buy'),
           'trading_action'] = 'buy next long position'

    df.loc[((df['prev_position_lagged'] == 'long_buy') & (df['position'] == 'out') ),
           'trading_action'] = 'sell previous long position'

    df.loc[(df['prev_position_lagged'] == 'out') & (df['position'] == 'short_sell'),
           'trading_action'] = 'sell next short position'

    df.loc[((df['prev_position_lagged'] == 'short_sell') & (df['position'] == 'out')),
           'trading_action'] = 'buy previous short position'

    df.loc[(df['prev_position_lagged'] == 'short_sell') & (df['position'] == 'long_buy'),
           'trading_action'] = 'buy previous short position and buy next long position'

    df.loc[(df['prev_position_lagged'] == 'long_buy') & (df['position'] == 'short_sell'),
           'trading_action'] = 'sell previous long position and sell next short position'
    last_indices = list()
    sell_longs = df[df['trading_action'] == 'sell previous long position'].index
    if len(sell_longs)>0:
        last_indices.append(sell_longs[-1])
    buy_shorts = df[df['trading_action'] == 'buy previous short position'].index
    if len(buy_shorts)>0:
        last_indices.append(buy_shorts[-1])
    if len(last_indices)>0:
        df.loc[df.index > max(last_indices), 'trading_action'] = ''
    trading_action_df = df[df['trading_action'] != ''].copy()

    if trading_action_df.shape[0] > 0:
        trading_action_df['gain_per_position'] = 0
        prev_capital_indices = list()
        if 'sell next short position' in trading_action_df['trading_action'].unique():
            prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'sell next short position'].index[0]
            prev_capital_indices.append(prev_short_sell_position_index)
        if 'buy next long position' in trading_action_df['trading_action'].unique():
            prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
            prev_capital_indices.append(prev_long_buy_position_index)
        prev_capital_index = min(prev_capital_indices)
        trading_action_df['current_capital'] = 0
        trading_action_df.loc[prev_capital_index, 'current_capital'] = initial_capital
        for i, row in trading_action_df.iterrows():
            if row['trading_action'] == 'buy next long position':
                prev_long_buy_position_index = i
                trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
            if row['trading_action'] == 'sell next short position':
                prev_short_sell_position_index = i
                trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
            if row['trading_action'] == 'buy previous short position and buy next long position':
                prev_long_buy_position_index = i
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, ind_price] - trading_action_df.loc[i, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                               trading_action_df.loc[prev_short_sell_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            if row['trading_action'] == 'sell previous long position and sell next short position':
                prev_short_sell_position_index = i
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, ind_price] - trading_action_df.loc[prev_long_buy_position_index, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                               trading_action_df.loc[prev_long_buy_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            if row['trading_action'] == 'sell previous long position':
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, ind_price] - trading_action_df.loc[prev_long_buy_position_index, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                              trading_action_df.loc[prev_long_buy_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
            if row['trading_action'] == 'buy previous short position':
                trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, ind_price] - trading_action_df.loc[i, ind_price]
                trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                              (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                               trading_action_df.loc[prev_short_sell_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                prev_capital_index = i
        if trading_action_df is not None:
            df = pd.merge(df,
                          trading_action_df[['gain_per_position', 'current_capital', 'trading_action']],
                          how='left',
                          left_index=True,
                          right_index=True)
            df['gain_per_position'].fillna(0.0, inplace=True)
            df['current_capital'].fillna(0.0, inplace=True)
            return df
    else:
        df['gain_per_position'] = 0.0
        df['current_capital'] = 0.0
        df['trading_action'] = ''
        return df



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
    prev_capital_index = min(prev_capital_indices)
    df.loc[prev_capital_index, 'current_capital'] = initial_capital

    tz_str = df.index[0][-6:]

    for i, row in df.iterrows():
        # ha a mostani capital rosszabb mint az i-edik sorban a price add el, és update-elj minden indexet!
        # különben mehet tovább lefelé!
        current_last_in_position_index = max([prev_long_buy_position_index, prev_short_sell_position_index])
        if row['current_capital'] - stop_loss_perc * df.loc[current_last_in_position_index, 'current_capital'] < 0:
            # add el:
            if current_last_in_position_index == prev_long_buy_position_index:
                prev_short_sell_position_index = i
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

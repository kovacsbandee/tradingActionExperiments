import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from data_sources.add_indicators import add_gradient, add_rolling_average
from plots.plots import create_histograms, create_candle_stick_chart_w_indicators_for_trendscalping


def add_strategy_specific_indicators(exp_data, averaged_cols=['close', 'volume'],
                                     ma_short=5, ma_long=12,
                                     shooth_win_len_short = 4,
                                     shooth_win_len_long = 4,
                                     plot_strategy_indicators=True):
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker]['trading_day_data']
        indicators = list()
        for col in averaged_cols:
            indicators.append(col)
            short_ind_col = f'{col}_ma{ma_short}'
            sticker_df[short_ind_col] = add_rolling_average(price_time_series=sticker_df,
                                                            col=col,
                                                            window_length=ma_short)
            indicators.append(short_ind_col)
            sticker_df[f'{short_ind_col}_grad'] = add_gradient(price_time_series=sticker_df,
                                                               col=short_ind_col)
            indicators.append(f'{short_ind_col}_grad')
            # sticker_df[f'{short_ind_col}_grad_smoothed_{shooth_win_len_short}'] = add_rolling_average(price_time_series=sticker_df,
            #                                                                                           col = f'{short_ind_col}_grad',
            #                                                                                           window_length=shooth_win_len_short)
            # indicators.append(f'{short_ind_col}_grad_smoothed_{shooth_win_len_short}')

            # sticker_df[f'{short_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df,
            #                                                     col=f'{short_ind_col}_grad')
            # indicators.append(f'{short_ind_col}_grad2')

            long_ind_col = f'{col}_ma{ma_long}'
            sticker_df[long_ind_col] = add_rolling_average(price_time_series=sticker_df, col=col, window_length=ma_long)
            indicators.append(long_ind_col)
            sticker_df[f'{long_ind_col}_grad'] = add_gradient(price_time_series=sticker_df, col=long_ind_col)
            indicators.append(f'{long_ind_col}_grad')
            # sticker_df[f'{long_ind_col}_grad_smoothed_{shooth_win_len_long}'] = add_rolling_average(price_time_series=sticker_df,
            #                                                                                           col = f'{long_ind_col}_grad',
            #                                                                                           window_length=shooth_win_len_long)
            # indicators.append(f'{long_ind_col}_grad_smoothed_{shooth_win_len_long}')

            '''
            sticker_df[f'{long_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df, col=f'{long_ind_col}')
            indicators.append(f'{long_ind_col}_grad2')
            '''
        if plot_strategy_indicators:
            # TODO itt van egy bug, mert nem különbözik a prev és a trading day data!
            # prev_day_sticker_df = sticker_df[pd.to_datetime(sticker_df.index).date == sticker_df.index[0].date()].copy()
            # create_histograms(plot_df=prev_day_sticker_df,
            #                   cols=indicators,
            #                   column_vars=averaged_cols,
            #                   plot_name=f'{sticker}_prev_day_indicators_indicators')
            # create_candle_stick_chart_w_indicators_for_trendscalping(
            #     plot_df=prev_day_sticker_df,
            #     sticker_name=sticker,
            #     averaged_cols=averaged_cols,
            #     indicators=indicators,
            #     plot_name='prev_day')
            trading_day_sticker_df = sticker_df[pd.to_datetime(sticker_df.index).date == sticker_df.index[-1].date()].copy()
            create_histograms(plot_df=trading_day_sticker_df,
                              cols=indicators,
                              column_vars=averaged_cols,
                              plot_name=f'{sticker}_trading_day_indicators')
            create_candle_stick_chart_w_indicators_for_trendscalping(
                plot_df=trading_day_sticker_df,
                sticker_name=sticker,
                averaged_cols=averaged_cols,
                indicators=indicators,
                plot_name='trading_day')

def apply_single_long_strategy(exp_data, day, ind_price='close', data='trading_day_data', ma_short=5, ma_long=12, initial_capital=3000, comission_ratio=0.0):
    results=list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        sticker_df.loc[(0.001 < sticker_df[f'{ind_price}_ma{ma_long}_grad']) & (0.001 < sticker_df[f'{ind_price}_ma{ma_short}_grad']), 'position'] = 'long_buy'
        #sticker_df.loc[(0.001 < sticker_df[f'{ind_price}_ma{ma_long}_grad']) | (0.001 < sticker_df[f'{ind_price}_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
        #todo ki kell próbálni a 2. feltétel nélkül is, illetve meg kell nézni ha benne van, akkor van-e olyan trade, ami csak emiatt kerül bele, ugy kene mukodnie, hogy osszefuggo poziciokat alkossan az elso feltetellel
        sticker_df.loc[(sticker_df['position'] == 'long_buy') & (sticker_df['prev_position_lagged'] == 'out'), 'trading_action'] = 'buy next long position'
        sticker_df.loc[(sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'long_buy'), 'trading_action'] = 'sell previous long position'
        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        sticker_df.loc[sticker_df.index > max(trading_action_df[trading_action_df['trading_action'] == 'sell previous long position'].index), 'trading_action'] = ''
        trading_action_df['gain_per_position'] = 0
        prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
        prev_capital_index = prev_long_buy_position_index
        trading_action_df['current_capital'] = 0
        trading_action_df.loc[prev_capital_index, 'current_capital'] = initial_capital
        if trading_action_df.shape[0] > 0:
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'sell previous long position':
                    trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, ind_price] - trading_action_df.loc[prev_long_buy_position_index, ind_price]
                    trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (
                                                                               trading_action_df.loc[i, 'gain_per_position'] * \
                                                                               (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                                                trading_action_df.loc[prev_long_buy_position_index, ind_price]))) - comission_ratio * \
                                                                  trading_action_df.loc[prev_capital_index, 'current_capital']
                    prev_capital_index = i
                if row['trading_action'] == 'buy next long position':
                    prev_long_buy_position_index = i
                    trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
            print(f'Gain on {sticker} with simple long strategy', trading_action_df.gain_per_position.sum())
            results.append((day, 'long', sticker, trading_action_df.gain_per_position.sum()))
            sticker_df = pd.merge(sticker_df, trading_action_df[['trading_action', 'gain_per_position', 'current_capital']],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain_per_position'].fillna(0.0, inplace=True)
            exp_data['stickers'][sticker]['trading_day_data_long_strategy'] = sticker_df
        else:
            sticker_df['gain_per_position'] = 0
            exp_data['stickers'][sticker]['trading_day_data_long_strategy'] = sticker_df
    return results

def apply_single_short_strategy(exp_data, day, ind_price='close', data='trading_day_data', ma_short=5, ma_long=12, initial_capital=3000, comission_ratio=0.0):
    results = list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        sticker_df.loc[(-0.001 > sticker_df[f'{ind_price}_ma{ma_long}_grad']) & (-0.001 > sticker_df[f'{ind_price}_ma{ma_short}_grad']), 'position'] = 'short_sell'
        #sticker_df.loc[(-0.001 > sticker_df[f'{ind_price}_ma{ma_long}_grad']) | (-0.001 > sticker_df[f'{ind_price}_ma{ma_short}_grad']), 'position'] = 'short_sell'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
        sticker_df.loc[(sticker_df['position'] == 'short_sell') & (sticker_df['prev_position_lagged'] == 'out'), 'trading_action'] = 'sell next short position'
        sticker_df.loc[(sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'short_sell'), 'trading_action'] = 'buy previous short position'
        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        sticker_df.loc[sticker_df.index > max(trading_action_df[trading_action_df['trading_action'] == 'buy previous short position'].index), 'trading_action'] = ''
        trading_action_df['gain_per_position'] = 0
        prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy previous short position'].index[0]
        prev_capital_index = prev_short_sell_position_index
        trading_action_df['current_capital'] = 0
        trading_action_df.loc[prev_capital_index, 'current_capital'] = initial_capital
        if trading_action_df.shape[0] > 0:
            trading_action_df['gain'] = 0
            prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'sell next short position'].index[0]
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'buy previous short position':
                    trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, ind_price] - trading_action_df.loc[i, ind_price]
                    trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                                  (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                                   trading_action_df.loc[prev_short_sell_position_index, ind_price]))) - comission_ratio * \
                                                                   trading_action_df.loc[prev_capital_index, 'current_capital']
                if row['trading_action'] == 'sell next short position':
                    prev_short_sell_position_index = i
                    trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital']
            print(f'Gain on {sticker} with simple short strategy', trading_action_df.gain_per_position.sum())
            results.append((day, 'short', sticker, trading_action_df.gain_per_position.sum()))
            sticker_df = pd.merge(sticker_df, trading_action_df[['gain_per_position', 'current_capital']],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain_per_position'].fillna(0.0, inplace=True)
            exp_data['stickers'][sticker]['trading_day_data_short_strategy'] = sticker_df
        else:
            sticker_df['gain_per_position'] = 0
            exp_data['stickers'][sticker]['trading_day_data_short_strategy'] = sticker_df
    return results

def apply_simple_combined_trend_following_strategy(exp_data, day, exp_name, ind_price='close', data='trading_day_data',
                                                   ma_short=5, ma_long=12,
                                                   shooth_win_len_long=4,
                                                   shooth_win_len_short=4,
                                                   short_epsilon = 0.02, long_epsilon = 0.002,
                                                   initial_capital=3000, comission_ratio=0.0):
    results = list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        sticker_df.loc[
            (long_epsilon < sticker_df[f'{ind_price}_ma{ma_long}_grad']) & (short_epsilon < sticker_df[f'{ind_price}_ma{ma_short}_grad']),
            'position'] = 'long_buy'
        sticker_df.loc[
            (-long_epsilon > sticker_df[f'{ind_price}_ma{ma_long}_grad']) & (-short_epsilon > sticker_df[f'{ind_price}_ma{ma_short}_grad']),
            'position'] = 'short_sell'
        # sticker_df.loc[
        #     (long_epsilon < sticker_df[f'{ind_price}_ma{ma_long}_grad_smoothed_{shooth_win_len_long}']) & (short_epsilon < sticker_df[f'{ind_price}_ma{ma_short}_grad_smoothed_{shooth_win_len_short}']),
        #     'position'] = 'long_buy'
        # sticker_df.loc[
        #     (-long_epsilon > sticker_df[f'{ind_price}_ma{ma_long}_grad_smoothed_{shooth_win_len_long}']) & (-short_epsilon > sticker_df[f'{ind_price}_ma{ma_short}_grad_smoothed_{shooth_win_len_short}']),
        #     'position'] = 'short_sell'


        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)

    #   for finding all the possible position and laggad position combination
    #    list(set(list(zip(df['prev_position_lagged'], df['position']))))

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'out') & (sticker_df['position'] == 'long_buy'),
                       'trading_action'] = 'buy next long position'

        sticker_df.loc[((sticker_df['prev_position_lagged'] == 'long_buy') & (sticker_df['position'] == 'out') ),
               'trading_action'] = 'sell previous long position'

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'out') & (sticker_df['position'] == 'short_sell'),
               'trading_action'] = 'sell next short position'

        sticker_df.loc[((sticker_df['prev_position_lagged'] == 'short_sell') & (sticker_df['position'] == 'out')),
               'trading_action'] = 'buy previous short position'

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'short_sell') & (sticker_df['position'] == 'long_buy'),
               'trading_action'] = 'buy previous short position and buy next long position'

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'long_buy') & (sticker_df['position'] == 'short_sell'),
               'trading_action'] = 'sell previous long position and sell next short position'

        last_indices = list()
        sell_longs = sticker_df[sticker_df['trading_action'] == 'sell previous long position'].index
        if len(sell_longs)>0:
            last_indices.append(sell_longs[-1])
        buy_shorts = sticker_df[sticker_df['trading_action'] == 'buy previous short position'].index
        if len(buy_shorts)>0:
            last_indices.append(buy_shorts[-1])
        if len(last_indices)>0:
            sticker_df.loc[sticker_df.index > max(last_indices), 'trading_action'] = ''


        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()

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
                    (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] / trading_action_df.loc[prev_long_buy_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                    prev_capital_index = i
                if row['trading_action'] == 'buy previous short position':
                    trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, ind_price] - trading_action_df.loc[i, ind_price]
                    trading_action_df.loc[i, 'current_capital'] = (trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                                  (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                                   trading_action_df.loc[prev_short_sell_position_index, ind_price]))) - comission_ratio * trading_action_df.loc[prev_capital_index, 'current_capital']
                    prev_capital_index = i
            print(f'Total gain per position on {sticker} with simple combined trend scalping strategy', trading_action_df.gain_per_position.sum())
            results.append((day, 'combined', sticker, trading_action_df.gain_per_position.sum()))
            sticker_df = pd.merge(sticker_df,
                                  trading_action_df[['gain_per_position', 'current_capital']],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain_per_position'].fillna(0.0, inplace=True)
            create_candle_stick_chart_w_indicators_for_trendscalping(plot_df=sticker_df,
                                                                     sticker_name=sticker,
                                                                     plot_name=f'{exp_name}_with_positions',
                                                                     indicators=['current_capital',
                                                                                 f'{ind_price}_ma{ma_short}',
                                                                                 f'{ind_price}_ma{ma_short}_grad',
                                                                                 f'{ind_price}_ma{ma_long}',
                                                                                 f'{ind_price}_ma{ma_long}_grad'])
            exp_data['stickers'][sticker]['trading_day_data_w_combined_strategy'] = sticker_df
        else:
            sticker_df['gain_per_position'] = 0
            sticker_df['current_capital'] = initial_capital
            exp_data['stickers'][sticker]['trading_day_data_w_combined_strategy'] = sticker_df
    return results


def apply_simple_combined_trend_following_strategy_w_stopping_crit(exp_data, day, exp_name, ind_price='close', data='trading_day_data',
                                                   ma_short=5, ma_long=12,
                                                   shooth_win_len_long=4,
                                                   shooth_win_len_short=4,
                                                   short_epsilon = 0.02, long_epsilon = 0.002,
                                                   initial_capital=3000, comission_ratio=0.0):
    results = list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df = sticker_df.iloc[:int(int(len(sticker_df.index)) / 2)].copy()
        sticker_df['position'] = 'out'
        sticker_df.loc[
            (long_epsilon < sticker_df[f'{ind_price}_ma{ma_long}_grad']) & (short_epsilon < sticker_df[f'{ind_price}_ma{ma_short}_grad']),
            'position'] = 'long_buy'
        sticker_df.loc[
            (-long_epsilon > sticker_df[f'{ind_price}_ma{ma_long}_grad']) & (-short_epsilon > sticker_df[f'{ind_price}_ma{ma_short}_grad']),
            'position'] = 'short_sell'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)

        # sticker_df.loc[
        #     (long_epsilon < sticker_df[f'{ind_price}_ma{ma_long}_grad_smoothed_{shooth_win_len_long}']) & (
        #                 short_epsilon < sticker_df[f'{ind_price}_ma{ma_short}_grad_smoothed_{shooth_win_len_short}']),
        #     'position'] = 'long_buy'
        # sticker_df.loc[
        #     (-long_epsilon > sticker_df[f'{ind_price}_ma{ma_long}_grad_smoothed_{shooth_win_len_long}']) & (
        #                 -short_epsilon > sticker_df[f'{ind_price}_ma{ma_short}_grad_smoothed_{shooth_win_len_short}']),
        #     'position'] = 'short_sell'

        #   for finding all the possible position and laggad position combination
    #    list(set(list(zip(df['prev_position_lagged'], df['position']))))

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'out') & (sticker_df['position'] == 'long_buy'),
               'trading_action'] = 'buy next long position'

        sticker_df.loc[((sticker_df['prev_position_lagged'] == 'long_buy') & (sticker_df['position'] == 'out') ),
               'trading_action'] = 'sell previous long position'

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'out') & (sticker_df['position'] == 'short_sell'),
               'trading_action'] = 'sell next short position'

        sticker_df.loc[((sticker_df['prev_position_lagged'] == 'short_sell') & (sticker_df['position'] == 'out')),
               'trading_action'] = 'buy previous short position'

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'short_sell') & (sticker_df['position'] == 'long_buy'),
               'trading_action'] = 'buy previous short position and buy next long position'

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'long_buy') & (sticker_df['position'] == 'short_sell'),
               'trading_action'] = 'sell previous long position and sell next short position'
        last_indices = list()
        sell_longs = sticker_df[sticker_df['trading_action'] == 'sell previous long position'].index
        if len(sell_longs)>0:
            last_indices.append(sell_longs[-1])
        buy_shorts = sticker_df[sticker_df['trading_action'] == 'buy previous short position'].index
        if len(buy_shorts)>0:
            last_indices.append(buy_shorts[-1])
        if len(last_indices)>0:
            sticker_df.loc[sticker_df.index > max(last_indices), 'trading_action'] = ''
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()

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
            print(f'Total gain per position on {sticker} with simple combined trend scalping strategy with time restriction', trading_action_df.gain_per_position.sum())
            results.append((day, 'combined_time_restriction', sticker, trading_action_df.gain_per_position.sum()))
            sticker_df = pd.merge(sticker_df,
                                  trading_action_df[['gain_per_position', 'current_capital']],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain_per_position'].fillna(0.0, inplace=True)
            create_candle_stick_chart_w_indicators_for_trendscalping(plot_df=sticker_df,
                                                                     sticker_name=sticker,
                                                                     plot_name=f'{exp_name}_with_positions_and_time_restriction',
                                                                     indicators=['current_capital',
                                                                                 f'{ind_price}_ma{ma_short}',
                                                                                 f'{ind_price}_ma{ma_short}_grad',
                                                                                 f'{ind_price}_ma{ma_long}',
                                                                                 f'{ind_price}_ma{ma_long}_grad'])
            exp_data['stickers'][sticker]['trading_day_data_w_combined_strategy'] = sticker_df
        else:
            sticker_df['gain_per_position'] = 0
            sticker_df['current_capital'] = initial_capital
            exp_data['stickers'][sticker]['trading_day_data_w_combined_strategy'] = sticker_df
    return results

'''
def apply_simple_combined_trend_following_strategy(exp_data, day, data='trading_day_data', epsilon = 0.001, ma_short=5, ma_long=12, initial_capital = 3000):
    results = list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        sticker_df.loc[(epsilon < sticker_df[f'close_ma{ma_long}_grad']) & (epsilon < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df.loc[(-epsilon > sticker_df[f'close_ma{ma_long}_grad']) & (-epsilon > sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'short_sell'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
        #   for finding all the possible position and laggad position combination
        #    list(set(list(zip(df['prev_position_lagged'], df['position']))))

        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'out') & (sticker_df['position'] == 'long_buy'), 'trading_action'] = 'buy next long position'
        sticker_df.loc[((sticker_df['prev_position_lagged'] == 'long_buy') & (sticker_df['position'] == 'out')), 'trading_action'] = 'sell previous long position'
        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'out') & (sticker_df['position'] == 'short_sell'), 'trading_action'] = 'sell next short position'
        sticker_df.loc[((sticker_df['prev_position_lagged'] == 'short_sell') & (sticker_df['position'] == 'out')), 'trading_action'] = 'buy previous short position'
        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'short_sell') & (sticker_df['position'] == 'long_buy'), 'trading_action'] = 'buy previous short position and buy next long position'
        sticker_df.loc[(sticker_df['prev_position_lagged'] == 'long_buy') & (sticker_df['position'] == 'short_sell'), 'trading_action'] = 'sell previous long position and sell next short position'

        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        sticker_df.loc[sticker_df.index > max(
            [max(trading_action_df[trading_action_df['trading_action'] == 'buy previous short position'].index), \
             max(trading_action_df[trading_action_df['trading_action'] == 'sell previous long position'].index)]), 'trading_action'] = ''
        trading_action_df['gain_per_position'] = 0
        prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'sell next short position'].index[0]
        prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
        prev_capital_index = min([prev_short_sell_position_index, prev_long_buy_position_index])
        trading_action_df['current_capital'] = 0
        trading_action_df.loc[prev_capital_index, 'current_capital'] = initial_capital
        if trading_action_df.shape[0] > 0:
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'buy next long position':
                    prev_long_buy_position_index = i
                if row['trading_action'] == 'sell previous long position':
                    trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, 'close'] - \
                                                                    trading_action_df.loc[prev_long_buy_position_index, 'close']
                    trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                                              (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                                                                               trading_action_df.loc[prev_long_buy_position_index, 'close']))
                    prev_capital_index = i
                if row['trading_action'] == 'sell next short position':
                    prev_short_sell_position_index = i
                if row['trading_action'] == 'buy previous short position':
                    trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, 'close'] - trading_action_df.loc[i, 'close']
                    trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                                                                              (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                                                                               trading_action_df.loc[prev_short_sell_position_index, 'close']))
                    prev_capital_index = i
                # if row['trading_action'] == 'buy previous short position and buy next long position':
                #     trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[prev_short_sell_position_index, 'close'] - trading_action_df.loc[i, 'close']
                #     trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                #                                                               (trading_action_df.loc[prev_short_sell_position_index, 'current_capital'] /
                #                                                                trading_action_df.loc[prev_short_sell_position_index, 'close']))
                #     prev_capital_index = i
                #     prev_long_buy_position_index = i
                # if row['trading_action'] == 'sell previous long position and sell next short position':
                #     trading_action_df.loc[i, 'gain_per_position'] = trading_action_df.loc[i, 'close'] - trading_action_df.loc[prev_long_buy_position_index, 'close']
                #     trading_action_df.loc[i, 'current_capital'] = trading_action_df.loc[prev_capital_index, 'current_capital'] + (trading_action_df.loc[i, 'gain_per_position'] * \
                #                                                               (trading_action_df.loc[prev_long_buy_position_index, 'current_capital'] /
                #                                                                trading_action_df.loc[prev_long_buy_position_index, 'close']))
                #     prev_capital_index = i
                #     prev_short_sell_position_index = i
            print(f'Gain on {sticker} with simple combined trend scalping strategy', trading_action_df.gain_per_position.sum())
            results.append((day, 'combined', sticker, trading_action_df.gain_per_position.sum()))
            sticker_df = pd.merge(sticker_df, trading_action_df[['gain_per_position', 'current_capital']],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain_per_position'].fillna(0.0, inplace=True)
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df
        else:
            sticker_df['gain_per_position'] = 0
            sticker_df['current_capital'] = initial_capital
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df
    return results
'''

def apply_strategy():
    '''
    Use lag and conditions
    For price search in the not as big times and choose the max from it!
    :return:
    '''
    pass


def calculate_gain_from_positions():
    pass
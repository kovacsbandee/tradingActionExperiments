import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

PROJ_PATH = 'F:/tradingActionExperiments'


from data_sources.add_indicators import add_gradient, add_rolling_average
from plots.plots import create_histograms, create_candle_stick_chart_w_indicators_for_trendscalping


def add_strategy_specific_indicators(exp_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12,
                                     plot_strategy_indicators=True):
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker]['trading_day_data']
        indicators = list()
        for col in averaged_cols:
            indicators.append(col)
            short_ind_col = f'{col}_ma{ma_short}'
            sticker_df[short_ind_col] = add_rolling_average(price_time_series=sticker_df, col=col,
                                                            window_length=ma_short)
            indicators.append(short_ind_col)
            sticker_df[f'{short_ind_col}_grad'] = add_gradient(price_time_series=sticker_df, col=short_ind_col)
            indicators.append(f'{short_ind_col}_grad')
            sticker_df[f'{short_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df,
                                                                col=f'{short_ind_col}_grad')
            indicators.append(f'{short_ind_col}_grad2')

            long_ind_col = f'{col}_ma{ma_long}'
            sticker_df[long_ind_col] = add_rolling_average(price_time_series=sticker_df, col=col, window_length=ma_long)
            indicators.append(long_ind_col)
            sticker_df[f'{long_ind_col}_grad'] = add_gradient(price_time_series=sticker_df, col=long_ind_col)
            indicators.append(f'{long_ind_col}_grad')
            sticker_df[f'{long_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df, col=f'{long_ind_col}')
            indicators.append(f'{long_ind_col}_grad2')
        if plot_strategy_indicators:
            prev_day_sticker_df = sticker_df[pd.to_datetime(sticker_df.index).date == sticker_df.index[0].date()].copy()
            create_histograms(plot_df=prev_day_sticker_df,
                              cols=indicators,
                              column_vars=averaged_cols,
                              plot_name=f'{sticker}_prev_day_indicators_indicators')
            create_candle_stick_chart_w_indicators_for_trendscalping(
                plot_df=prev_day_sticker_df,
                sticker_name=sticker,
                averaged_cols=averaged_cols,
                indicators=indicators,
                plot_name='prev_day')
            prev_day_sticker_df = sticker_df[pd.to_datetime(sticker_df.index).date == sticker_df.index[0].date()].copy()
            create_histograms(plot_df=prev_day_sticker_df,
                              cols=indicators,
                              column_vars=averaged_cols,
                              plot_name=f'{sticker}_trading_day_indicators')
            create_candle_stick_chart_w_indicators_for_trendscalping(
                plot_df=prev_day_sticker_df,
                sticker_name=sticker,
                averaged_cols=averaged_cols,
                indicators=indicators,
                plot_name='trading_day')

def apply_single_long_strategy(exp_data, day, data='trading_day_data', ma_short=5, ma_long=12, num_stocks=1):
    results=list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        sticker_df.loc[(0.001 < sticker_df[f'close_ma{ma_long}_grad']) & (0.001 < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df.loc[(0.001 < sticker_df[f'close_ma{ma_long}_grad']) | (0.001 < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
        #todo ki kell próbálni a 2. feltétel nélkül is, illetve meg kell nézni ha benne van, akkor van-e olyan trade, ami csak emiatt kerül bele, ugy kene mukodnie, hogy osszefuggo poziciokat alkossan az elso feltetellel
        sticker_df.loc[(sticker_df['position'] == 'long_buy') & (sticker_df['prev_position_lagged'] == 'out'), 'trading_action'] = 'buy next long position'
        sticker_df.loc[(sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'long_buy'), 'trading_action'] = 'sell previous long position'
        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        if trading_action_df.shape[0] > 0:
            sticker_df.loc[sticker_df.index > max(trading_action_df[trading_action_df['trading_action'] == 'sell previous long position'].index), 'trading_action'] = ''
            trading_action_df['gain'] = 0
            prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'sell previous long position':
                    trading_action_df.loc[i, 'gain'] = trading_action_df.loc[i, 'close'] - trading_action_df.loc[prev_long_buy_position_index, 'close'] * num_stocks
                if row['trading_action'] == 'buy next long position':
                    prev_long_buy_position_index = i
            print(f'Gain on {sticker} with simple long strategy', trading_action_df.gain.sum())
            results.append((day, 'combined', sticker, trading_action_df.gain.sum()))
            sticker_df = pd.merge(sticker_df, trading_action_df['gain'],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain'].fillna(0.0, inplace=True)
        else:
            sticker_df['gain'] = 0
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df
    return results

def apply_single_short_strategy(exp_data, day, data='trading_day_data', ma_short=5, ma_long=12, num_stocks=1):
    results = list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        sticker_df.loc[(-0.001 > sticker_df[f'close_ma{ma_long}_grad']) & (-0.001 > sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'short_sell'
        sticker_df.loc[(-0.001 > sticker_df[f'close_ma{ma_long}_grad']) | (-0.001 > sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'short_sell'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
        sticker_df.loc[(sticker_df['position'] == 'short_sell') & (sticker_df['prev_position_lagged'] == 'out'), 'trading_action'] = 'sell next short position'
        sticker_df.loc[(sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'short_sell'), 'trading_action'] = 'buy previous short position'
        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        if trading_action_df.shape[0] > 0:
            sticker_df.loc[sticker_df.index > max(trading_action_df[trading_action_df['trading_action'] == 'buy previous short position'].index), 'trading_action'] = ''
            trading_action_df['gain'] = 0
            prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'sell next short position'].index[0]
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'buy previous short position':
                    trading_action_df.loc[i, 'gain'] = trading_action_df.loc[prev_short_sell_position_index, 'close'] - trading_action_df.loc[i, 'close']  * num_stocks
                if row['trading_action'] == 'sell next short position':
                    prev_short_sell_position_index = i
            print(f'Gain on {sticker} with simple short strategy', trading_action_df.gain.sum())
            results.append((day, 'combined', sticker, trading_action_df.gain.sum()))
            sticker_df = pd.merge(sticker_df, trading_action_df['gain'],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain'].fillna(0.0, inplace=True)
        else:
            sticker_df['gain'] = 0
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df
    return results

def apply_simple_combined_trend_following_strategy(exp_data, day, data='trading_day_data', ma_short=5, ma_long=12, num_stocks=1):
    results = list()
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        epsilon = 0.001
        sticker_df.loc[(epsilon < sticker_df[f'close_ma{ma_long}_grad']) & (epsilon < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df.loc[(-epsilon > sticker_df[f'close_ma{ma_long}_grad']) & (-epsilon > sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'short_sell'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)

        sticker_df.loc[
            ((sticker_df['position'] == 'long_buy') & (sticker_df['prev_position_lagged'] == 'out')) | \
            ((sticker_df['position'] == 'long_buy') & (sticker_df['prev_position_lagged'] == 'short_sell')),
            'trading_action'] = 'buy next long position'

        sticker_df.loc[
            ((sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'long_buy')),
            'trading_action'] = 'sell previous long position'

        sticker_df.loc[
            ((sticker_df['position'] == 'short_sell') & (sticker_df['prev_position_lagged'] == 'out')) | \
            ((sticker_df['position'] == 'short_sell') & (sticker_df['prev_position_lagged'] == 'long_buy')),
            'trading_action'] = 'sell next short position'

        sticker_df.loc[
            ((sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'short_sell')),
            'trading_action'] = 'buy previous short position'

        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        if trading_action_df.shape[0] > 0:
            sticker_df.loc[sticker_df.index > max(
                [max(trading_action_df[trading_action_df['trading_action'] == 'buy previous short position'].index), \
                 max(trading_action_df[trading_action_df['trading_action'] == 'sell previous long position'].index)]), 'trading_action'] = ''
            trading_action_df['gain'] = 0
            prev_short_sell_position_index = trading_action_df[trading_action_df['trading_action'] == 'sell next short position'].index[0]
            prev_long_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'buy previous short position':
                    trading_action_df.loc[i, 'gain'] = trading_action_df.loc[prev_short_sell_position_index, 'close'] - trading_action_df.loc[i, 'close']  * num_stocks
                if row['trading_action'] == 'sell next short position':
                    prev_short_sell_position_index = i
                if row['trading_action'] == 'sell previous long position':
                    trading_action_df.loc[i, 'gain'] = trading_action_df.loc[i, 'close'] - trading_action_df.loc[prev_long_buy_position_index, 'close'] * num_stocks
                if row['trading_action'] == 'buy next long position':
                    prev_long_buy_position_index = i

            print(f'Gain on {sticker} with simple combined trend scalping strategy', trading_action_df.gain.sum())
            results.append((day, 'combined', sticker, trading_action_df.gain.sum()))
            sticker_df = pd.merge(sticker_df, trading_action_df['gain'],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain'].fillna(0.0, inplace=True)
        else:
            sticker_df['gain'] = 0
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df
    return results


def apply_strategy():
    '''
    Use lag and conditions
    For price search in the not as big times and choose the max from it!
    :return:
    '''
    pass


def calculate_gain_from_positions():
    pass
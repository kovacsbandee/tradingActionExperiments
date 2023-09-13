import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

PROJ_PATH = 'F:/tradingActionExperiments'


from data_sources.add_indicators import add_gradient, add_rolling_average
from plots.plots import create_histograms, create_candle_stick_chart_w_indicators_for_trendscalping

strategy_name = 'trendScalping'
#exp_data = experiment_data
sticker = 'COMP'
#sticker_df = exp_data['stickers'][sticker]['data']
indicators =  []


def add_strategy_specific_indicators(exp_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True):
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker]['data']
        indicators = list()
        for col in averaged_cols:
            indicators.append(col)
            short_ind_col = f'{col}_ma{ma_short}'
            sticker_df[short_ind_col] = add_rolling_average(price_time_series=sticker_df, col=col, window_length=ma_short)
            indicators.append(short_ind_col)
            sticker_df[f'{short_ind_col}_grad'] = add_gradient(price_time_series=sticker_df, col=short_ind_col)
            indicators.append(f'{short_ind_col}_grad')
            sticker_df[f'{short_ind_col}_grad2'] = add_gradient(price_time_series=sticker_df, col=f'{short_ind_col}_grad')
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
                              plot_name=f'{sticker}_indicators')
            create_candle_stick_chart_w_indicators_for_trendscalping(
                plot_df=prev_day_sticker_df,
                sticker_name=sticker,
                averaged_cols=averaged_cols,
                indicators=indicators)


def apply_strategy():
    '''
    Use lag and conditions
    For price search in the not as big times and choose the max from it!
    :return:
    '''
    pass


def calculate_gain_from_positions():
    pass
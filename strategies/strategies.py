import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

PROJ_PATH = 'F:/tradingActionExperiments'


from data_sources.add_indicators import add_gradient, add_rolling_average
from plots.plots import create_histograms, create_candle_stick_chart_w_indicators_for_trendscalping

strategy_name = 'trendScalping'
exp_data = experiment_data
sticker = 'COMP'
sticker_df = exp_data['stickers'][sticker]['data']
indicators =  []


def add_strategy_specific_indicators(averaged_cols=['close', 'volume'], rolling_average_win_lens=[5,9,10], plot_strategy_indicators = False):
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker]['data']
        for col in averaged_cols:
            indicators.append(col)
            for win_len in rolling_average_win_lens:
                new_column = f'{col}_ma{win_len}'
                sticker_df[new_column] = add_rolling_average(price_time_series=sticker_df, col=col, window_length=win_len)
                sticker_df[f'{new_column}_grad'] = add_gradient(price_time_series=sticker_df, col=new_column)
                indicators.append(new_column)
                indicators.append(f'{new_column}_grad')
        if plot_strategy_indicators:
            prev_day_sticker_df = sticker_df[pd.to_datetime(sticker_df.index).date == sticker_df.index[0].date()].copy()
            create_histograms(plot_df=prev_day_sticker_df,
                              cols=indicators,
                              column_vars=averaged_cols,
                              plot_name=f'{sticker}_indicators')
            create_candle_stick_chart_w_indicators_for_trendscalping(
                plot_df=prev_day_sticker_df,
                sticker_name=sticker)


def apply_strategy():
    '''
    Use lag and conditions
    For price search in the not as big times and choose the max from it!
    :return:
    '''
    pass


def calculate_gain_from_positions():
    pass
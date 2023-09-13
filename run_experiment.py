from scanners.scanners import get_nasdaq_stickers, andrewAzizRecommendedScanner
from data_sources.generate_price_data import generatePriceData
from random import sample
from strategies.strategies import add_strategy_specific_indicators

# initial variables:
TRADING_DAY = '2023-08-25'
experiment_data = dict()
experiment_data['trading_day'] = TRADING_DAY
experiment_data['stickers'] = dict()

# 1) get watchlist
#nasdaq_stickers = sample(get_nasdaq_stickers(), 1000) + ['MRVL']

azis_scanner = andrewAzizRecommendedScanner(trading_day=TRADING_DAY)
azis_scanner.get_filtering_stats()
azis_scanner.recommend_premarket_watchlist()
stickers = azis_scanner.recommended_stickers


for sticker in stickers:
    experiment_data['stickers'][sticker] = dict()

# 2) load trading day data
get_price_data = generatePriceData(date=TRADING_DAY, exp_dict=experiment_data)
get_price_data.load_watchlist_daily_price_data()


from plots.plots import create_histograms, create_candle_stick_chart_w_indicators_for_trendscalping
from data_sources.add_indicators import add_gradient,add_rolling_average


import pandas as pd

def add_strategy_specific_indicators(exp_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True):
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker]['data']
        indicators = list()
        for col in averaged_cols:
            indicators.append(col)
            short_ind_col = f'{col}_ma{ma_short}'
            sticker_df[short_ind_col] = add_rolling_average(price_time_series=sticker_df, col=col, window_length=ma_short)
            sticker_df[f'{short_ind_col}_grad'] = add_gradient(price_time_series=sticker_df, col=short_ind_col)
            indicators.append(short_ind_col)
            indicators.append(f'{short_ind_col}_grad')
            long_ind_col = f'{col}_ma{ma_long}'
            sticker_df[long_ind_col] = add_rolling_average(price_time_series=sticker_df, col=col, window_length=ma_long)
            sticker_df[f'{long_ind_col}_grad'] = add_gradient(price_time_series=sticker_df, col=long_ind_col)
            indicators.append(long_ind_col)
            indicators.append(f'{long_ind_col}_grad')
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


add_strategy_specific_indicators(exp_data=experiment_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True)

exp_data = experiment_data
ma_short=5
ma_long=12


def apply_strategy_for_trend_scalping():
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker]['data']
        sticker_df['position'] = 'out'
        sticker_df.loc[sticker_df['Close_ma5_grad'].isna(), 'position'] = 'no_position'

        sticker_df.loc[(ma_grad_eps_limit < sticker_df['Close_ma5_grad']) & \
                       (0 < sticker_df['Close_ma5_grad2']), 'position'] = 'long_buy'
        sticker_df.loc[(-ma_grad_eps_limit > sticker_df['Close_ma5_grad']) & \
                       (0 > sticker_df['Close_ma5_grad2']), 'position'] = 'sell_short'
        sticker_df['trading_action'] = ''
        prev1_position = 'out'
        for i, row in sticker_df.iterrows():
            current_position = row['position']
            if prev1_position == 'no_position' and current_position == 'long_buy':
                sticker_df.loc[i, 'trading_action'] = 'buy next long position'
            if prev1_position == 'no_position' and current_position == 'sell_short':
                sticker_df.loc[i, 'trading_action'] = 'sell next short position'
            if prev1_position == 'out' and current_position == 'long_buy':
                sticker_df.loc[i, 'trading_action'] = 'buy next long position'
            if prev1_position == 'long_buy' and current_position == 'out':
                sticker_df.loc[i, 'trading_action'] = 'sell previous long position'
            if prev1_position == 'out' and current_position == 'sell_short':
                sticker_df.loc[i, 'trading_action'] = 'sell next short position'
            if prev1_position == 'sell_short' and current_position == 'out':
                sticker_df.loc[i, 'trading_action'] = 'buy previous short position'
            if prev1_position == 'sell_short' and current_position == 'long_buy':
                sticker_df.loc[i, 'trading_action'] = 'buy previous short position and buy next long position'
            if prev1_position == 'long_buy' and current_position == 'sell_short':
                sticker_df.loc[i, 'trading_action'] = 'sell previous long position and sell next short position'
            prev1_position = current_position
        exp_data['trading_day_data'][sticker] = sticker_df

def apply_strategy():
    '''
    Use lag and conditions
    For price search in the not as big times and choose the max from it!
    :return:
    '''
    pass



'''
experiment_data structure
    # stickers as keys
        # price data
        # strategy parameters
            # name
            # details
        # scanner name
        # gains
        # plot names = list()


3) Apply strategy
4) Analyse results
'''
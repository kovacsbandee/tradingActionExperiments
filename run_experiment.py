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
                              plot_name=f'{sticker}_indicators')
            create_candle_stick_chart_w_indicators_for_trendscalping(
                plot_df=prev_day_sticker_df,
                sticker_name=sticker,
                averaged_cols=averaged_cols,
                indicators=indicators)
            #todo el kell készíteni a fenti két plot-ot is a trading day-re!

add_strategy_specific_indicators(exp_data=experiment_data, averaged_cols=['close', 'volume'], ma_short=5, ma_long=12, plot_strategy_indicators = True)




def apply_single_long_strategy(exp_data, data='trading_day_data', ma_short=5, ma_long=12, num_stocks=1):
    for sticker in exp_data['stickers'].keys():
        sticker_df = exp_data['stickers'][sticker][data]
        sticker_df['position'] = 'out'
        #TODO epsiolon has to be optimized!!!
        sticker_df.loc[(0.001 < sticker_df[f'close_ma{ma_long}_grad']) & (0.001 < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df.loc[(0.001 < sticker_df[f'close_ma{ma_long}_grad']) | (0.001 < sticker_df[f'close_ma{ma_short}_grad']), 'position'] = 'long_buy'
        sticker_df['trading_action'] = ''
        sticker_df['prev_position_lagged'] = sticker_df['position'].shift(1)
        #todo ki kell próbálni a 2. feltétel nélkül is, illetve meg kell nézni ha benne van, akkor van-e olyan önálló trade, ami csak emiatt kerül bele, 
        # illetve ugy kene mukodnie, hogy osszefuggo poziciokat alkossan az elso feltetellel, ezt ellenorizninkell es ha nem igy mukodik javitani
        sticker_df.loc[(sticker_df['position'] == 'long_buy') & (sticker_df['prev_position_lagged'] == 'out'), 'trading_action'] = 'buy next long position'
        sticker_df.loc[(sticker_df['position'] == 'out') & (sticker_df['prev_position_lagged'] == 'long_buy'), 'trading_action'] = 'sell previous long position'
        sticker_df.drop('prev_position_lagged', axis=1, inplace=True)
        trading_action_df = sticker_df[sticker_df['trading_action'] != ''].copy()
        if trading_action_df.shape[0] > 0:
            sticker_df.loc[sticker_df.index > max(trading_action_df[trading_action_df['trading_action'] == 'sell previous long position'].index), 'trading_action'] = ''
            trading_action_df['gain'] = 0
            prev_buy_position_index = trading_action_df[trading_action_df['trading_action'] == 'buy next long position'].index[0]
            for i, row in trading_action_df.iterrows():
                if row['trading_action'] == 'sell previous long position':
                    trading_action_df.loc[i, 'gain'] = trading_action_df.loc[i, 'close'] - trading_action_df.loc[prev_buy_position_index, 'close'] * num_stocks
                if row['trading_action'] == 'buy next long position':
                    prev_buy_position_index = i
            print(f'Gain on {sticker} with simple long strategy', trading_action_df.gain.sum())
            sticker_df = pd.merge(sticker_df, trading_action_df['gain'],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain'].fillna(0.0, inplace=True)
        else:
            sticker_df['gain'] = 0
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df

apply_single_long_strategy(exp_data=experiment_data)


def apply_single_short_strategy(exp_data, data='trading_day_data', ma_short=5, ma_long=12, num_stocks=1):
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
            sticker_df = pd.merge(sticker_df, trading_action_df['gain'],
                                  how='left',
                                  left_index=True,
                                  right_index=True)
            sticker_df['gain'].fillna(0.0, inplace=True)
        else:
            sticker_df['gain'] = 0
            exp_data['stickers'][sticker]['trading_day_data'] = sticker_df

apply_single_short_strategy(exp_data=experiment_data)




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
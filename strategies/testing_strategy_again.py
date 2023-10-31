import pandas as pd
import numpy as np
from itertools import product
from datetime import datetime, timedelta, time

price_col='close'
ma_short=5
ma_long=12
short_epsilon=0.01
long_epsilon=0.01

initial_capital = 3000
comission_ratio = 0.0
stop_loss_perc = 0.0

short_grad = f'{price_col}_ma{ma_short}_grad'
long_grad = f'{price_col}_ma{ma_long}_grad'


# long_filter = (long_epsilon < df[long_grad]) & (short_epsilon < df[short_grad])
# short_filter = (-long_epsilon > df[long_grad]) & (-short_epsilon > df[short_grad])



df = pd.read_csv('F:/tradingActionExperiments_database/stockwise_database/TSLA.csv', index_col='Datetime')
df.index = pd.to_datetime(df.index.str[:-6])

basedf = pd.merge(pd.DataFrame(index = [datetime.combine(d, t) for d,t in list(product(np.unique(df.index.date), np.unique(df.index.time)))]),
                  df,
                  how='left',
                  left_index=True,
                  right_index=True)
basedf.fillna(method='ffill', inplace=True)
# this one has to contain each row form window_df and the bar data has to be join-ed to it
to_database = pd.DataFrame(index=basedf.index)

# window_df has to be initialized here from the first ma_long+1 message

window_df = pd.DataFrame(basedf.iloc[0:ma_long][price_col]).copy()
prev_long_buy_index = 0
prev_short_sell_index = 0
window_df['current_capital'] = 0
for i, row in pd.DataFrame(basedf.iloc[ma_long:][price_col]).iterrows():
    new_row_df = pd.DataFrame(dict(zip(row.index, [[e] for e in row.values])))
    new_row_df.index = [i]
    window_df = pd.concat([window_df, new_row_df])
    window_df[short_grad] = window_df[price_col].rolling(ma_short, center=False).mean().diff()
    window_df[long_grad] = window_df[price_col].rolling(ma_long, center=False).mean().diff()
    window_df['position'] = 'out'
    window_df.loc[(long_epsilon < window_df[long_grad]) & (short_epsilon < window_df[short_grad]), 'position'] = 'long_buy'
    window_df.loc[(-long_epsilon > window_df[long_grad]) & (-short_epsilon > window_df[short_grad]), 'position'] = 'short_sell'
    # calculate current capital
    if window_df.loc[i, 'position'] == 'out':
        window_df.loc[i, 'current_capital'] = window_df.loc[i - timedelta(minutes=1), 'current_capital']
    if window_df.loc[i, 'position'] == 'long_buy':
        window_df.loc[i, 'current_capital'] = window_df.loc[i - timedelta(minutes=1), 'current_capital'] + \
                                         (window_df.loc[i, price_col] - window_df.loc[i - timedelta(minutes=1), price_col]) * \
                                         (window_df.loc[i - timedelta(minutes=1), 'current_capital'] / \
                                          window_df.loc[i - timedelta(minutes=1), price_col])
    if window_df.loc[i, 'position'] == 'short_sell':
        window_df.loc[i, 'current_capital'] = window_df.loc[i - timedelta(minutes=1), 'current_capital'] + \
                                         (window_df.loc[i - timedelta(minutes=1), price_col] - window_df.loc[i, price_col]) * \
                                         (initial_capital / \
                                          window_df.loc[i - timedelta(minutes=1), price_col])
    if window_df.loc[i - timedelta(minutes=1), 'position'] == 'out' and window_df.loc[i, 'position'] == 'long_buy':
        prev_long_buy_index = i
        window_df.loc[prev_long_buy_index, 'trading_action'] = 'buy next long position'
        if prev_short_sell_index == 0:
            prev_capital_index = i
            window_df.loc[prev_capital_index, 'current_capital'] = initial_capital
    if window_df.loc[i - timedelta(minutes=1), 'position'] == 'out' and window_df.loc[i, 'position'] == 'short_sell':
        prev_short_sell_index = i
        window_df.loc[prev_short_sell_index, 'trading_action'] = 'sell next short position'
        if prev_long_buy_index == 0:
            prev_capital_index = i
            window_df.loc[prev_capital_index, 'current_capital'] = initial_capital
print(window_df)
print(prev_long_buy_index)
print(prev_short_sell_index)
print(prev_capital_index)



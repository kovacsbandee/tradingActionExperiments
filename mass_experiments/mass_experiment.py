import os
from itertools import chain

import pandas as pd
from joblib import Parallel, delayed
from strategies.strategy_for_mass_experiments import add_strategy_specific_indicators, apply_simple_combined_trend_following_strategy

import plotly.graph_objects as go
from plotly.subplots import make_subplots


PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = f'{PROJ_PATH}/data_store/database'

short_ma = 5
long_ma = 12
experiment_description = f'test_w_combined_strategy_ma{short_ma}_ma{long_ma}'

def get_all_file_w_paths():
    all_file = list(chain.from_iterable(
        [[f'{DB_PATH}/{dir}/csvs/{f}' for f in os.listdir(f'{DB_PATH}/{dir}/csvs') if all([l.isupper() for l in f.rstrip('.csv')])]
         for dir in os.listdir(DB_PATH)]))
    return all_file

def create_strategy_results(csv):
    sticker_df = pd.read_csv(csv)
    sticker_df = sticker_df[['Datetime' ,'open', 'high', 'low', 'close', 'adj close', 'volume']]
    sticker_df.set_index('Datetime', inplace=True)
    date = csv[65:75].replace('_', '-')
    sticker = csv.split('/')[-1][:-4]
    avg_close = sticker_df['close'].mean()
    avg_volume = sticker_df['volume'].mean()
    if len(sticker_df) < 195:
        final_capital = 0
        total_gain = 0
    else:
        sticker_df = add_strategy_specific_indicators(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
        sticker_df = apply_simple_combined_trend_following_strategy(df=sticker_df, ma_short=short_ma, ma_long=long_ma)
        capitals = sticker_df[sticker_df['current_capital'] != 0.0]['current_capital']
        final_capital = 0.0 if len(capitals) == 0 else capitals[-1]
        total_gain = sticker_df['gain_per_position'].sum()
    save_file_name = csv.rstrip('.csv') + '_' + experiment_description + '.csv'
    sticker_df.to_csv(save_file_name, mode='w+')
    result = [date, sticker, avg_close, avg_volume, final_capital, total_gain]
    return result

def run_parallel_strategy_operations(all_csvs, exp_desc):
    # results = list()
    # for csv in all_csvs:
    #     res = create_strategy_results(csv=csv)
    #     results.append(res)
    results = Parallel(n_jobs=16)(delayed(create_strategy_results)(csv) for csv in all_csvs)
    results = chain.from_iterable(results)
    result_df = pd.DataFrame.from_records(results, columns=['date', 'sticker', 'avg_close', 'avg_volume', 'final_capital', 'total_gain'])
    result_df.to_csv(f'{PROJ_PATH}/data_store/results/{exp_desc}.csv')
    return result_df

def create_candle_stick_chart_w_indicators_for_trendscalping(plot_df,
                                                             sticker_name,
                                                             averaged_cols=[],
                                                             indicators=['close_ma5', 'close_ma12'],
                                                             plot_name=''):
    for c in averaged_cols:
        if c in indicators:
            indicators.remove(c)
    fig = make_subplots(rows=2+len(indicators), cols=1, shared_xaxes=True)
    fig.add_trace(go.Candlestick(x=plot_df.index,
                                 open=plot_df['open'],
                                 high=plot_df['high'],
                                 low=plot_df['low'],
                                 close=plot_df['close'],
                                 name=sticker_name), row=1, col=1)
    fig.add_trace(go.Bar(x=plot_df.index,
                         y=plot_df['volume'],
                         name='Volume'), row=2, col=1)
    for i, indicator in enumerate([col for col in indicators if col not in averaged_cols]):
        fig.add_trace(go.Scatter(x=plot_df.index,
                                 y=plot_df[f'{indicator}'],
                                 name=f'{indicator}',
                                 mode='lines',
                                 connectgaps=True), row=3+i, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False,
                      height=1500)
    fig.write_html(f'{PROJ_PATH}/data_store/results/plots/candle_stick_chart_{sticker_name}_{plot_name}.html')


files = get_all_file_w_paths()

res_df = run_parallel_strategy_operations(all_csvs=files, exp_desc=experiment_description)


plots = res_df[res_df['final_capital'] > 3150]

for i, row in plots.iterrows():
    d = row['date'].replace('-', '_')
    s = row['sticker']
    print(d,s)
    df = pd.read_csv(f'{DB_PATH}/stock_prices_for_{d}/csvs/{s}_{experiment_description}.csv')
    create_candle_stick_chart_w_indicators_for_trendscalping(plot_df=df,
                                                             sticker_name=s,
                                                             plot_name=f'{experiment_description}_with_positions_{d}',
                                                             indicators=['current_capital',
                                                                         f'close_ma{short_ma}',
                                                                         f'close_ma{short_ma}_grad',
                                                                         f'close_ma{long_ma}',
                                                                         f'close_ma{long_ma}_grad'])

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_daily_statistics(data_man):
    plot_df = pd.read_csv(f'{data_man.db_path}/{data_man.daily_dir}/recommended_symbols_pre_market_stats.csv')
    statistics_variables = [c for c in plot_df.columns if c != 'symbol']

    fig = make_subplots(rows=len(statistics_variables), cols=1, subplot_titles=statistics_variables)
    for i, stat in enumerate(statistics_variables):
        fig.add_trace(go.Bar(x=plot_df['symbol'],
                             y=plot_df[stat]), row=i+1, col=1)
    fig.write_html(f'{data_man.db_path}/{data_man.daily_dir}/daily_statistics.html')


def create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(data_gen, data_man):
    date = data_man.run_parameters['trading_day']

    for symbol in data_gen.symbol_dict.keys():
        plot_df = data_gen.symbol_dict[symbol]['symbol_dataframe']
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                            specs=[[{"secondary_y": False}],
                                   [{"secondary_y": True}],
                                   [{"secondary_y": False}],
                                   [{"secondary_y": False}]])
        fig.add_trace(go.Candlestick(x=plot_df.index,
                                     open=plot_df['o'],
                                     high=plot_df['h'],
                                     low=plot_df['l'],
                                     close=plot_df['c'],
                                     name=symbol), row=1, col=1)
        fig.add_trace(go.Bar(x=plot_df.index,
                             y=plot_df['v'],
                             showlegend=False,
                             hovertext='volume',
                             marker={'color': 'blue'}),
                      secondary_y=False, row=2, col=1)
        fig.update_yaxes(title='volume', title_font=dict(color='blue'), secondary_y=False, row=2, col=1)
        fig.add_trace(go.Bar(x=plot_df.index,
                             y=plot_df['n'],
                             hovertext='number of transactions',
                             showlegend=False,
                             marker={'color': 'red'}),
                      secondary_y=True, row=2, col=1)
        fig.update_yaxes(title = 'number of transactions', title_font=dict(color='red'), autorange = 'reversed', secondary_y=True, row=2, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index,
                                 y=plot_df['open_norm'],
                                 name='normalized price',
                                 mode='lines',
                                 connectgaps=True), row=3, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index,
                                 y=plot_df['open_small_indicator'],
                                 name='small_indicator',
                                 mode='lines',
                                 connectgaps=True), row=4, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index,
                                 y=plot_df['open_big_indicator'],
                                 name='big_indicator',
                                 mode='lines',
                                 connectgaps=True), row=5, col=1)
        fig.update_xaxes(showticklabels=True)
        title_date = date.replace('-', '.')
        fig.update_layout(title=f'{symbol} {title_date}.', title_font=dict(size=18), xaxis_rangeslider_visible=False, height=1500)
        fig.write_html(f'{data_man.db_path}/{data_man.daily_dir_name}/daily_files/plots/candle_plot_{symbol}_{date}.html')
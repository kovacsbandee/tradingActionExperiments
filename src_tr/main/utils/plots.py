import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src_tr.main.enums_and_constants.trading_constants import *

def plot_daily_statistics(plot_df, db_path, daily_dir_name):
    statistics_variables = [c for c in plot_df.columns if c != 'symbol']
    fig = make_subplots(rows=len(statistics_variables), cols=1, subplot_titles=statistics_variables)
    for i, stat in enumerate(statistics_variables):
        fig.add_trace(go.Bar(x=plot_df['symbol'],
                             y=plot_df[stat],
                             name=stat), row=i+1, col=1)
    fig.update_layout(height=len(statistics_variables) * 200)
    fig.write_html(f'{db_path}/{daily_dir_name}/daily_statistics.html')

def plot_daily_statistics_correlation_matrix(plot_df, db_path, daily_dir_name):
    corr_df = plot_df[[c for c in plot_df.columns if c != 'symbol']].corr()
    fig = go.Figure(data=go.Heatmap(x=corr_df.columns,
                                    y=corr_df.index,
                                    z=corr_df))
    fig.write_html(f'{db_path}/{daily_dir_name}/daily_correlation_matrix.html')


def create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(data_gen, data_man):
    date = data_man.run_parameters['trading_day']

    for symbol in data_gen.sticker_dict.keys():
        plot_df = data_gen.sticker_dict[symbol]['sticker_dataframe']
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                            specs=[[{"secondary_y": False}],
                                   [{"secondary_y": True}],
                                   [{"secondary_y": False}],
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
                             showlegend=True,
                             name='volume',
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
                                 y=plot_df[OPEN_NORM],
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
        # TODO ide bele kell tenni az indikátorok hisztogramját és az epsilont is rá kell tenni a plotra.
        title_date = date.replace('-', '.')
        fig.update_layout(title=f'{symbol} {title_date}.', title_font=dict(size=18), xaxis_rangeslider_visible=False, height=1500)
        fig.write_html(f'{data_man.db_path}/{data_man.daily_dir_name}/daily_files/plots/candle_plot_{symbol}_{date}.html')
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

def get_marker_df(plot_df, db_path, daily_dir_name, symbol, date):
    plot_df = plot_df.loc[(plot_df['trading_action'] != '')]
    marker_df = plot_df[plot_df['trading_action'] != 'no_action'].copy()
    marker_df['position_symbols'] = np.nan
    marker_df.loc[marker_df['trading_action'] == 'buy_next_long_position', 'position_symbols'] = 'arrow-right'
    marker_df.loc[marker_df['trading_action'] == 'sell_previous_long_position', 'position_symbols'] = 'arrow-left'
    marker_df.loc[marker_df['trading_action'] == 'sell_previous_long_position_inner_stop_loss', 'position_symbols'] = 'arrow-left'
    marker_df.loc[marker_df['trading_action'] == 'sell_next_short_position', 'position_symbols'] = 'arrow-right'
    marker_df.loc[marker_df['trading_action'] == 'buy_previous_short_position', 'position_symbols'] = 'arrow-left'
    marker_df.loc[marker_df['trading_action'] == 'buy previous short position and buy next long position', 'position_symbols'] = 'diamond'
    marker_df.loc[marker_df['trading_action'] == 'sell previous long position and sell next short position', 'position_symbols'] = 'diamond'
    marker_df = marker_df[~marker_df['position_symbols'].isna()]
    return marker_df

def daily_time_series_charts(symbol_dict,
                             date,
                             epsilon,
                             mode,
                             db_path,
                             daily_dir_name):
    epsilon_line_width = 0.5
    for symbol in symbol_dict.keys():
        plot_df = symbol_dict[symbol]['daily_price_data_df']
        if mode == 'YF_DB':
            plot_df.drop('n', inplace=True, axis=1)
        time_dimension = plot_df.index
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                            specs=[[{"secondary_y": False}],
                                   [{"secondary_y": True if 'n' in plot_df.columns else False}],
                                   #[{"secondary_y": False}],
                                   #[{"secondary_y": False}],
                                   [{"secondary_y": False}],
                                   [{"secondary_y": False}],
                                   [{"secondary_y": False}]])
        fig.add_trace(go.Candlestick(x=time_dimension,
                                     open=plot_df['o'],
                                     high=plot_df['h'],
                                     low=plot_df['l'],
                                     close=plot_df['c'],
                                     name=symbol), row=1, col=1)
        marker_df = get_marker_df(plot_df, db_path=db_path, daily_dir_name=daily_dir_name, symbol=symbol, date=date)
        fig.add_trace(go.Scatter(x=marker_df.index,
                                 y=marker_df['o'],
                                 mode='markers',
                                 name='in and out position markers',
                                 hovertext=marker_df['trading_action'],
                                 marker_color='yellow',
                                 marker_symbol=marker_df['position_symbols'],
                                 marker_size=4), row=1, col=1)
        fig.add_trace(go.Bar(x=time_dimension,
                             y=plot_df['v'],
                             showlegend=False,
                             hovertext='volume',
                             marker={'color': 'blue'}),
                      secondary_y=False, row=2, col=1)
        fig.update_yaxes(title='volume', title_font=dict(color='blue'), secondary_y=False, row=2, col=1)
        if 'n' in plot_df.columns:
            fig.add_trace(go.Bar(x=time_dimension,
                                 y=plot_df['n'],
                                 hovertext='number of transactions',
                                 showlegend=False,
                                 marker={'color': 'red'}),
                          secondary_y=True, row=2, col=1)
            fig.update_yaxes(title = 'number of transactions', title_font=dict(color='red'), autorange = 'reversed', secondary_y=True, row=2, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=np.where(plot_df['current_capital'] < plot_df['current_capital'].mean()*0.05, np.nan, plot_df['current_capital']),
                                 name='current_capital',
                                 mode='lines',
                                 marker=dict(color='blue'),
                                 connectgaps=True), row=3, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=plot_df['open_small_indicator'],
                                 name='small_indicator',
                                 mode='lines',
                                 marker={'color': 'orange'},
                                 connectgaps=True), row=4, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='orange',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=4, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[-epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='orange',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=4, col=1)
        # fig.add_trace(go.Histogram(x=plot_df['open_small_indicator'],
        #                            name='open_small_indicator_hist',
        #                            nbinsx=100), row=5, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=plot_df['open_big_indicator'],
                                 name='big_indicator',
                                 mode='lines',
                                 marker={'color': 'purple'},
                                 connectgaps=True), row=5, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='purple',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=5, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[-epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='purple',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=5, col=1)
        # fig.add_trace(go.Histogram(x=plot_df['open_big_indicator'],
        #                            name='open_big_indicator_hist',
        #                            nbinsx=100), row=7, col=1)
        fig.update_xaxes(showticklabels=True)
        fig.update_layout(title=f'{symbol} {date}.', title_font=dict(size=18), xaxis_rangeslider_visible=False, height=1500)
        fig.write_html(f'{db_path}/{daily_dir_name}/daily_files/plots/candle_plot_{symbol}_{date}.html')


def daily_statistic_charts(symbol_dict,
                             date,
                             epsilon,
                             mode,
                             db_path,
                             daily_dir_name):
    epsilon_line_width = 0.5
    for symbol in symbol_dict.keys():
        plot_df = symbol_dict[symbol]['daily_price_data_df']
        if mode == 'YF_DB':
            plot_df.drop('n', inplace=True, axis=1)
        time_dimension = plot_df.index
        fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                            specs=[[{"secondary_y": False}],
                                   [{"secondary_y": True if 'n' in plot_df.columns else False}],
                                   #[{"secondary_y": False}],
                                   #[{"secondary_y": False}],
                                   [{"secondary_y": False}],
                                   [{"secondary_y": False}],
                                   [{"secondary_y": False}]])
        fig.add_trace(go.Candlestick(x=time_dimension,
                                     open=plot_df['o'],
                                     high=plot_df['h'],
                                     low=plot_df['l'],
                                     close=plot_df['c'],
                                     name=symbol), row=1, col=1)
        marker_df = get_marker_df(plot_df, db_path=db_path, daily_dir_name=daily_dir_name, symbol=symbol, date=date)
        fig.add_trace(go.Scatter(x=marker_df.index,
                                 y=marker_df['o'],
                                 mode='markers',
                                 name='in and out position markers',
                                 hovertext=marker_df['trading_action'],
                                 marker_color='yellow',
                                 marker_symbol=marker_df['position_symbols'],
                                 marker_size=4), row=1, col=1)
        fig.add_trace(go.Bar(x=time_dimension,
                             y=plot_df['v'],
                             showlegend=False,
                             hovertext='volume',
                             marker={'color': 'blue'}),
                      secondary_y=False, row=2, col=1)
        fig.update_yaxes(title='volume', title_font=dict(color='blue'), secondary_y=False, row=2, col=1)
        if 'n' in plot_df.columns:
            fig.add_trace(go.Bar(x=time_dimension,
                                 y=plot_df['n'],
                                 hovertext='number of transactions',
                                 showlegend=False,
                                 marker={'color': 'red'}),
                          secondary_y=True, row=2, col=1)
            fig.update_yaxes(title = 'number of transactions', title_font=dict(color='red'), autorange = 'reversed', secondary_y=True, row=2, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=np.where(plot_df['current_capital'] < plot_df['current_capital'].mean()*0.05, np.nan, plot_df['current_capital']),
                                 name='current_capital',
                                 mode='lines',
                                 marker=dict(color='blue'),
                                 connectgaps=True), row=3, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=plot_df['open_small_indicator'],
                                 name='small_indicator',
                                 mode='lines',
                                 marker={'color': 'orange'},
                                 connectgaps=True), row=4, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='orange',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=4, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[-epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='orange',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=4, col=1)
        # fig.add_trace(go.Histogram(x=plot_df['open_small_indicator'],
        #                            name='open_small_indicator_hist',
        #                            nbinsx=100), row=5, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=plot_df['open_big_indicator'],
                                 name='big_indicator',
                                 mode='lines',
                                 marker={'color': 'purple'},
                                 connectgaps=True), row=5, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='purple',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=5, col=1)
        fig.add_trace(go.Scatter(x=time_dimension,
                                 y=[-epsilon for i in range(len(time_dimension))],
                                 mode='lines',
                                 showlegend=False,
                                 line=dict(color='purple',
                                           width=epsilon_line_width),
                                 connectgaps=True), row=5, col=1)
        # fig.add_trace(go.Histogram(x=plot_df['open_big_indicator'],
        #                            name='open_big_indicator_hist',
        #                            nbinsx=100), row=7, col=1)
        fig.update_xaxes(showticklabels=True)
        fig.update_layout(title=f'{symbol} {date}.', title_font=dict(size=18), xaxis_rangeslider_visible=False, height=1500)
        fig.write_html(f'{db_path}/{daily_dir_name}/daily_files/plots/candle_plot_{symbol}_{date}.html')
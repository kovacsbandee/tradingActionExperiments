import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots



#def create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(symbol_csv):
for s in ['ALT', 'CLSK', 'CYTK', 'HUT', 'MARA']:
    symbol_csv = f'{s}_2023-12-28_0.0015_long_stop_loss_last_in_position.csv'
    plot_df = pd.read_csv(symbol_csv, index_col='t')
    symbol = symbol_csv.split('_')[0]
    date = symbol_csv.split('_')[1]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
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
                             y=plot_df['open_small_indicator'],
                             name='small_indicator',
                             mode='lines',
                             connectgaps=True), row=3, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index,
                             y=plot_df['open_big_indicator'],
                             name='big_indicator',
                             mode='lines',
                             connectgaps=True), row=4, col=1)
    fig.update_xaxes(showticklabels=True)
    title_date = date.replace('-', '.')
    fig.update_layout(title=f'{symbol} {title_date}.', title_font=dict(size=18), xaxis_rangeslider_visible=False, height=1500)
    fig.write_html(f'candle_plot_{symbol}_{date}.html')
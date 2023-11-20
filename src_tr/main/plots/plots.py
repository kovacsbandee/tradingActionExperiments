import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src_tr.main.data_sources.add_indicators import add_gradient

PROJ_PATH = 'F:/tradingActionExperiments'

def create_histograms(plot_df: pd.DataFrame,
                      cols: list=None,
                      column_vars: list=None,
                      plot_name: str = ''):
    if cols is None:
        plot_vars = plot_df.columns
    else:
        plot_vars = cols
    fig = make_subplots(rows=len(plot_vars) if column_vars==None else round(len(plot_vars)/len(column_vars)),
                        cols=1 if column_vars==None else len(column_vars),
                        subplot_titles=plot_vars,
                        vertical_spacing=0.07)
    if column_vars is None:
        for i, c in enumerate(plot_vars):
            fig.add_trace(go.Histogram(x=plot_df[c],
                                       showlegend=False,
                                       nbinsx=100), row=i+1, col=1)
            fig.update_xaxes(title=c, row=i + 1, col=1)
    if column_vars is not None:
        for j, col_var in enumerate(column_vars):
            for i, c in enumerate([c for c in plot_vars if col_var in c]):
                fig.add_trace(go.Histogram(x=plot_df[c],
                                           showlegend=False,
                                           nbinsx=100), row=i+1, col=1+j)
                #fig.update_xaxes(title = c,row=i+1, col=1+j)
    fig.update_layout(height=len(plot_vars)*100 if column_vars is None else int(len(plot_vars)/2)*150)
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/histograms/{plot_name}_hist.html')


def create_time_series_plots(plot_df: pd.DataFrame,
                             plot_vars: list = None,
                             bar_vars: list=['volume'],
                             plot_name: str=''):
    ts_variables = list(plot_df.columns) if plot_vars == None else plot_vars
    fig = make_subplots(rows=len(ts_variables),
                        cols=1,
                        row_titles=ts_variables,
                        shared_xaxes=True,
                        shared_yaxes=True)
    for i, col in enumerate(ts_variables):
        if col not in bar_vars:
            fig.add_trace(go.Scatter(name=col, x=plot_df.index, y=plot_df[col]), row=i+1, col=1)
        else:
            fig.add_trace(go.Bar(name=col, x=plot_df.index, y=plot_df[col]), row=i+1, col=1)
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/{plot_name}_ts.html')
    print('plot is ready')


def create_candle_stick_chart_w_indicators_for_trendscalping(plot_df,
                                                             sticker_name,
                                                             averaged_cols=['close', 'volume'],
                                                             indicators=['close_ma5', 'close_ma9'],
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
    if 'trading_action' in plot_df.columns:
        marker_df = plot_df.loc[plot_df['trading_action'] != ''].copy()
        #marker_df['trading_price'] = 0
        # marker_df.loc[marker_df['trading_action'] == 'buy next long position', 'trading_price'] = marker_df.loc[marker_df['trading_action'] == 'buy next long position', 'close']
        # marker_df.loc[marker_df['trading_action'] == 'sell previous long position', 'trading_price'] = marker_df.loc[marker_df['trading_action'] == 'sell previous long position', 'close']
        marker_df['symbols'] = '0'
        marker_df.loc[marker_df['trading_action'] == 'buy next long position', 'symbols'] = 'arrow-right'
        marker_df.loc[marker_df['trading_action'] == 'sell previous long position', 'symbols'] = 'arrow-left'
        marker_df.loc[marker_df['trading_action'] == 'sell next short position', 'symbols'] = 'arrow-right'
        marker_df.loc[marker_df['trading_action'] == 'buy previous short position', 'symbols'] = 'arrow-left'
        marker_df.loc[marker_df['trading_action'] == 'buy previous short position and buy next long position', 'symbols'] = 'diamond'
        marker_df.loc[marker_df['trading_action'] == 'sell previous long position and sell next short position', 'symbols'] = 'diamond'
        fig.add_trace(go.Scatter(x=marker_df.index,
                                 y=marker_df['close'],
                                 mode='markers',
                                 #name='in and out price markers',
                                 hovertext=marker_df['trading_action'],
                                 marker_color='yellow',
                                 marker_symbol=marker_df['symbols']), row=1, col=1)
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
    date = plot_df.index[-1].date().strftime('%Y-%m-%d')
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/candle_stick_charts/candle_stick_chart_{sticker_name}_{date}_{plot_name}.html')

'''
ezeknek majd az analyzers-ben lesz a helye
'''
# TODO:
def relative_volume_in_time_for_all_stock():
    '''
    This method should plot on a bar chart the relative volume in each minute averaged over all the stocks in the experiment data.
    :return:
    '''


def compare_prev_and_trading_day_stats():
    '''
    Most még nem tudom megfogalmazni, hogy mit kell csinálni, csak tudom, hogy majd kell!
    Valahogyan a profitalbilitással össze kell vetni!
    :return:
    '''
    pass
    
def create_histogram_for_derivatives():
    '''
    Az epsilon jó beállításához, legalább arra van szükseg, hogy a long és short MA deriváltjainak
    eloszlását egy hisztogramon ábrázolni kell az összes stock-ra ami a scan-ből kijön amíg ad adatot a yf(last month)
    '''
    pass


def create_gain_histograms(gain_file = 'gains_from_0815.csv'):
    plot_df = pd.read_csv(f'{PROJ_PATH}/data_store/{gain_file}')
    pos_types = plot_df['position_type'].unique()
    fig = make_subplots(cols=1, rows=len(pos_types))
    for i, position_type in enumerate(pos_types):
            fig.add_trace(go.Histogram(x=plot_df[plot_df['position_type'] == position_type]['gain_per_stock'],
                                       name=position_type,
                                       nbinsx=40,
                                       histnorm='probability'), col=1,  row=i+1)
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/gain_histograms_for_{gain_file[:-4]}.html')
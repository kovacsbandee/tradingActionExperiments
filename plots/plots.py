import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJ_PATH = 'F:/tradingActionExperiments'

def create_histograms(plot_df: pd.DataFrame, excluded_cols: list, plot_name: str):
    plot_vars = [c for c in plot_df.columns if c not in excluded_cols]
    fig = make_subplots(rows=len(plot_vars),
                        cols=1,
                        row_titles=plot_vars)
    for i, c in enumerate(plot_vars):
        fig.add_trace(go.Histogram(name=c, x=plot_df[c]), row=i+1, col=1)
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/{plot_name}.html')


def create_time_series_plots(plot_df: pd.DataFrame,
                             plot_vars: list,
                             bar_vars: list=['volume']):
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
    plot_name = f'STICKER_DATE'
    fig.write_html(f'{PROJ_PATH}/plots/plot_store/{plot_name}.html')
    print('plot is ready')

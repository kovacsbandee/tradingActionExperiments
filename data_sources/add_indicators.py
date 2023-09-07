import pandas as pd
import numpy as np

def add_rolling_average(price_time_series: pd.DataFrame, col: str, window_length: int=10):
    '''
    returns a pandas column
    :param price_time_series:
    :param col:
    :return:
    '''
    return price_time_series[col].rolling(window_length, center=False).mean()

def add_gradient(price_time_series: pd.DataFrame, col: str):
    '''
    returns a pandas column
    :param price_time_series:
    :param col:
    :return:
    '''
    return price_time_series[col].diff()

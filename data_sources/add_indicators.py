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


def add_MACD(price_time_series: pd.DataFrame, col: str, short_macd: int=2, long_macd: int=5):
    '''
    TODO a mozgóátlagok ablak hossza tuningolandó, a trend hossz eloszlások alapján,
    első közelítésben a macd napokban van megadva, de ez lehet más átlagolási hossz is...
    '''
    price_time_series[f'MACD_{short_macd}_{long_macd}'] = add_rolling_average(price_time_series, col=col, window_length=short_macd) - \
                                                          add_rolling_average(price_time_series, col=col, window_length=long_macd)
    return price_time_series[f'MACD_{short_macd}_{long_macd}']


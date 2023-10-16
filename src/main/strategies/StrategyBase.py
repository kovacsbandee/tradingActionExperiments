from abc import ABC, abstractmethod
from pandas import DataFrame

class StrategyBase(ABC):

    """
        sticker_dict = {
            'AAPL' : DataFrame,
            'TSLA' : DataFrame,
            . . .
        }
    """
    
    def __init__(self, sticker_dict_from_generator: dict):
        self.sticker_dict = sticker_dict_from_generator

    def add_rolling_average(self, price_time_series: DataFrame, col: str, window_length: int):
        return price_time_series[col].rolling(window_length, center=False).mean()

    def add_gradient(self, price_time_series: DataFrame, col: str):
        return price_time_series[col].diff()
    
    @abstractmethod
    def apply_strategy():
        pass
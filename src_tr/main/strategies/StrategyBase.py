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
    
    def __init__(self, sticker_dict_from_generator: dict=None):
        self.sticker_dict = sticker_dict_from_generator

    
    @abstractmethod
    def apply_strategy():
        pass
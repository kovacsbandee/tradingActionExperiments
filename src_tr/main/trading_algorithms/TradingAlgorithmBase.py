from abc import ABC, abstractmethod
from pandas import DataFrame

class TradingAlgorithmBase(ABC):

    """
        symbol_dict = {
            'AAPL' : DataFrame,
            'TSLA' : DataFrame,
            . . .
        }
    """
    
    def __init__(self, symbol_dict_from_generator: dict=None):
        self.symbol_dict = symbol_dict_from_generator

    
    @abstractmethod
    def apply_long_trading_algorithm():
        pass
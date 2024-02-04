from typing import List
from datetime import datetime
from abc import ABC, abstractmethod
from pandas import DataFrame
from alpaca.data.historical import StockHistoricalDataClient

class PriceDataGeneratorBase(ABC):
    
    trading_day: datetime
    recommended_symbol_list: List[str]
    symbol_dict: dict
    """
    symbol_dict = {
        'AAPL': 'symbol_df' : DataFrame [{"T":"b",
                                        "S":"AAPL",
                                        "o":171.68,
                                        "h":171.68,
                                        "l":171.585,
                                        "c":171.605,
                                        "v":1961,
                                        "t":"2023-10-03T18:16:00Z",
                                        "n":22,
                                        "vw":171.618957}],
        'MSFT': [],
        'TSLA': []
    }
    """
    
    def __init__(self,
                 recommended_symbol_list):
        self.recommended_symbol_list = recommended_symbol_list
        
    #@abstractmethod
    #def load_individual_symbol_data(self):
    #    pass
    
    @abstractmethod
    def load_watchlist_daily_price_data(self):
        pass

    @abstractmethod
    def update_symbol_df():
        pass
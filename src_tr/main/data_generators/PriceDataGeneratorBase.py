from typing import List
from datetime import datetime
from abc import ABC, abstractmethod
from pandas import DataFrame
from alpaca.data.historical import StockHistoricalDataClient

class PriceDataGeneratorBase(ABC):
    
    trading_day: datetime
    recommended_sticker_list: List[str]
    lower_price_boundary: int
    upper_price_boundary: int
    lower_volume_boundary: int
    prev_day_data: DataFrame
    prev_day_sticker_stats: dict
    trading_day_sticker_stats: dict #nem köll?
    
    sticker_dict: dict = dict()
    """
    sticker_dict = {
        'AAPL': 'sticker_df' : DataFrame [{"T":"b",
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
    data_window_size: int #nem köll?
    
    def __init__(self,
                 recommended_sticker_list):
        self.recommended_sticker_list = recommended_sticker_list
        
    #@abstractmethod
    #def load_individual_sticker_data(self):
    #    pass
    
    @abstractmethod
    def load_watchlist_daily_price_data(self):
        pass

    @abstractmethod
    def update_sticker_df():
        pass
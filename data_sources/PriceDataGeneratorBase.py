from datetime import datetime
from abc import ABC, abstractmethod
from pandas import DataFrame

class PriceDataGeneratorBase(ABC):
    
    trading_day: datetime
    sticker_data: DataFrame
    exp_dict: dict
    lower_price_boundary: int
    upper_price_boundary: int
    lower_volume_boundary: int
    
    def __init__(self, trading_day, sticker_data, exp_dict, lower_price_boundary, 
                 upper_price_boundary, lower_volume_boundary):
        self.trading_day = trading_day
        self.sticker_data = sticker_data
        self.exp_dict = exp_dict
        self.lower_price_boundary = lower_price_boundary
        self.upper_price_boundary = upper_price_boundary
        self.lower_volume_boundary = lower_volume_boundary
        
    @abstractmethod
    def load_individual_sticker_data(self):
        pass
    
    @abstractmethod
    def load_watchlist_daily_price_data(self):
        pass
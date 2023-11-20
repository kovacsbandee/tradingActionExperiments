from typing import List
from datetime import datetime
from abc import ABC, abstractmethod
import pandas as pd

class ScannerBase(ABC):
    
    #project_path: str
    trading_day: datetime 
    scanning_day: datetime # nem kell, származtatjuk
    stickers: List[str]
    pre_market_stats: List
    recommended_stickers: pd.DataFrame

    def __init__(self, 
                 #project_path,
                 trading_day, 
                 scanning_day, 
                 stickers):
        #self.project_path = project_path
        self.trading_day = trading_day
        self.scanning_day = scanning_day # TODO: lehet, hogy származtatni kéne? egyszerűbb lenne...
        self.stickers = stickers
        self.recommended_stickers = None
        
    @abstractmethod
    def get_pre_market_stats(self, sticker: str)  -> dict:
        pass
    
    @abstractmethod
    def calculate_filtering_stats(self, save_csv: bool = False) -> List:
        pass
    
    @abstractmethod
    def recommend_premarket_watchlist(self) -> List:
        pass
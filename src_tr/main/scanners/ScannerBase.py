from typing import List
from datetime import datetime
from abc import ABC, abstractmethod
import pandas as pd

class ScannerBase(ABC):
    
    #project_path: str
    trading_day: datetime 
    scanning_day: datetime # nem kell, származtatjuk
    symbols: List[str]
    pre_market_stats: List
    recommended_symbols: pd.DataFrame

    def __init__(self, 
                 #project_path,
                 trading_day, 
                 scanning_day, 
                 symbols):
        #self.project_path = project_path
        self.trading_day = trading_day
        self.scanning_day = scanning_day # TODO: lehet, hogy származtatni kéne? egyszerűbb lenne...
        self.symbols = symbols
        self.recommended_symbols = None
        
    @abstractmethod
    def get_pre_market_stats(self, symbol: str)  -> dict:
        pass
    
    @abstractmethod
    def calculate_filtering_stats(self, save_csv: bool = False) -> List:
        pass
    
    @abstractmethod
    def recommend_premarket_watchlist(self) -> List:
        pass
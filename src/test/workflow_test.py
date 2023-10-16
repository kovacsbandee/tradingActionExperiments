import os
from dotenv import load_dotenv
from checks.checks import check_trading_day
from utils.utils import calculate_scanning_day, get_nasdaq_stickers

from src.main.scanners.AndrewAzizRecommendedScanner import AndrewAzizRecommendedScanner
from src.main.data_generators.AlpacaPriceDataGenerator import AlpacaPriceDataGenerator

load_dotenv()
PROJECT_PATH = os.environ["PROJECT_PATH"]
STICKER_CSV_PATH = os.environ["STICKER_CSV_PATH"]

# 1) Scanner inicializálása -> watchlist létrehozás
trading_day = check_trading_day('2023-10-16')
scanning_day = calculate_scanning_day(trading_day)
stickers = get_nasdaq_stickers(project_path=PROJECT_PATH, file_path=STICKER_CSV_PATH)
scanner = AndrewAzizRecommendedScanner(name="AzizScanner",
                                       trading_day=trading_day,
                                       scanning_day=scanning_day,
                                       stickers=stickers,
                                       lower_price_boundary=10,
                                       upper_price_boundary=100,
                                       price_range_perc_cond=10,
                                       avg_volume_cond=25000)
#scanner.calculate_filtering_stats(save_csv=False)
#rec_st_list = scanner.recommend_premarket_watchlist()
rec_st_list = ["ALPN","APLS","BLFS"]
#print([s for s in rec_st_list])

# 2) PriceDataGenerator inicializálás
data_generator = AlpacaPriceDataGenerator(trading_day=trading_day,
                                          recommended_sticker_list=rec_st_list,
                                          lower_price_boundary=10,
                                          upper_price_boundary=100,
                                          lower_volume_boundary=0,
                                          data_window_size=10)
data_generator.initialize_sticker_dict()
data_generator.initialize_current_data_window()

minute_bars = [
    {"T":"b",
    "S":"ALPN",
    "o":171.68,
    "h":171.68,
    "l":171.585,
    "c":171.605,
    "v":1961,
    "t":"2023-10-03T18:16:00Z",
    "n":22,
    "vw":171.618957},
    
    {"T":"b",
    "S":"APLS",
    "o":171.68,
    "h":171.68,
    "l":171.585,
    "c":171.605,
    "v":1961,
    "t":"2023-10-03T18:16:00Z",
    "n":22,
    "vw":171.618957},
    
    {"T":"b",
    "S":"BLFS",
    "o":171.68,
    "h":171.68,
    "l":171.585,
    "c":171.605,
    "v":1961,
    "t":"2023-10-03T18:16:00Z",
    "n":22,
    "vw":171.618957}
]

data_generator.update_current_data_window(minute_bars=minute_bars)

minute_bars2 = [
    {"T":"b",
    "S":"ALPN",
    "o":171.68,
    "h":171.68,
    "l":171.585,
    "c":171.605,
    "v":1961,
    "t":"2023-10-03T18:17:00Z",
    "n":22,
    "vw":171.618957},
    
    {"T":"b",
    "S":"APLS",
    "o":171.68,
    "h":171.68,
    "l":171.585,
    "c":171.605,
    "v":1961,
    "t":"2023-10-03T18:17:00Z",
    "n":22,
    "vw":171.618957},
    
    {"T":"b",
    "S":"BLFS",
    "o":171.68,
    "h":171.68,
    "l":171.585,
    "c":171.605,
    "v":1961,
    "t":"2023-10-03T18:17:00Z",
    "n":22,
    "vw":171.618957}
]

data_generator.update_current_data_window(minute_bars=minute_bars2)
print(data_generator.current_data_window['ALPN'])

# 3) Stratégia, DataStream, TradingClient inicializálás
#NOTE: stop_loss_strategy_test.py

# 4) WebSocket inicializálás (ping interval fontos!)

# 5) TradingManager inicializálás, priceData ősfeltöltés
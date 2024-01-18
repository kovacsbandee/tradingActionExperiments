import os
from datetime import datetime
from dotenv import load_dotenv
from src_tr.main.utils.utils import get_nasdaq_stickers
from polygon import RESTClient
import pandas as pd
from joblib import Parallel, delayed

"""
    Bar data list format:
    
    [{'open': 128.075, 
    'high': 128.54, 
    'low': 128.075, 
    'close': 128.5,
    'volume': 3381, 
    'vwap': 128.3901, 
    'timestamp': 1701700260000, 
    'transactions': 91, 
    'otc': None}, 
    {...}, {...}]
"""

load_dotenv()
STICKER_CSV_PATH = os.environ["STICKER_CSV_PATH"]
nasdaq_stickers = get_nasdaq_stickers(file_path=STICKER_CSV_PATH)

def get_bar_data(ticker: str, from_: str, to: str):
    aggs = []
    client = RESTClient(api_key="Rdcy29x7wooeMAlqKIsnTfDiHOaz0J_d")
    aggregate_list = client.list_aggs(ticker=ticker, multiplier=1, timespan="minute", from_=from_, to=to, limit=50000)
    try:
        for a in aggregate_list:
            a_dict = a.__dict__
            ts = int(a.timestamp)
            ts /= 1000
            convert_ts = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            a_dict['timestamp'] = convert_ts
            a_dict['symbol'] = ticker
            aggs.append(a_dict)
    except Exception as ex:
        print(f'Error: {ex}')
    return aggs

bar_data_list_per_symbol = Parallel(n_jobs=-10, verbose=10)(delayed(get_bar_data)(ticker=e, from_="2022-12-01", to="2023-12-01") for e in nasdaq_stickers)

for e in bar_data_list_per_symbol:
    if len(e) > 0:
        bar_dict_list = []
        for i in e:
            bar_dict_list.append(i)
            
        if bar_dict_list:
            bar_df = pd.DataFrame(bar_dict_list)
            bar_df.set_index('timestamp', inplace=True)
            print(bar_df)
            pd.DataFrame(bar_df).to_csv(f"src_tr/test/polygon_test/bar_dfs/{e[0]['symbol']}.csv")
            
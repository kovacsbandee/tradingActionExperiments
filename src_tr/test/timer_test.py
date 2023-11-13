import time
from datetime import datetime

from src_tr.main.helpers.get_latest_bar_data import get_yahoo_data

while True:
    start_time = time.time() #epoch seconds e.g.: 1699788456.5225582
    now = time.localtime() 
    print(f"{now.tm_hour}:{now.tm_min}:{now.tm_sec}")
    
    yahoo_start = datetime(2023, 11, 10)
    yahoo_end = datetime(2023, 11, 11)
    bar_df = get_yahoo_data(sticker='AAPL', start_date=yahoo_start, end_date=yahoo_end,n_last_bars=1)
    print(bar_df)

    # The thing to time. Using sleep as an example
    time.sleep(10)
    

    """
        start_time = 1699788456.5225582
        time module params:
          timezone: -3600 (CET)
          tzname: ('CET', 'CEST')
    
    """
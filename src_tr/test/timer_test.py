import time
from datetime import datetime

from src_tr.main.utils.get_latest_bar_data import get_yahoo_data

while True:
    start_time = time.time() #epoch seconds e.g.: 1699788456.5225582
    now = time.localtime() 
    print(f"{now.tm_hour}:{now.tm_min}:{now.tm_sec}")

    time.sleep(1)
    

    """
        start_time = 1699788456.5225582
        time module params:
          timezone: -3600 (CET)
          tzname: ('CET', 'CEST')
    
    """
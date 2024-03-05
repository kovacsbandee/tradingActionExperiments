import pandas as pd
from datetime import datetime, timedelta
import pytz
import dateutil.parser as parser

#sample_date = '2024-02-22T14:31:00Z'
#parser_sample = parser.parse(sample_date)
#parse_sample = datetime.strptime(sample_date, '%Y-%m-%dT%H:%M:%SZ')

data = {"timestamp" : [datetime(2024, 1, 14, 12, 30, 5), 
                       datetime(2024, 3, 3, 14, 5, 10)], 
        "price" : [180.21, 
                   181.5]}

current_minute = datetime.now(pytz.timezone("UTC"))
test_df = pd.DataFrame(data)
test_df.set_index("timestamp", inplace=True)
if test_df.index[-1].minute == (current_minute-timedelta(minutes=2)).minute:

    new_row = test_df.iloc[-1:].copy()
    new_row.index = new_row.index + timedelta(minutes=1)

    test_df = pd.concat([test_df, new_row])
    test_df = test_df.sort_index()

    print(test_df)
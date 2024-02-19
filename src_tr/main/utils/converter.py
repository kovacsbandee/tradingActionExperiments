import json
import pandas as pd


def string_to_dict_list(input_string):
    try:
        data_list = json.loads(input_string)
        return data_list
    except json.JSONDecodeError as e:
        print(str(e))
    
def polygon_dict_to_dataframe(bar_dict: dict) -> pd.DataFrame:
    pass
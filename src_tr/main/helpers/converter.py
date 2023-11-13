import json
import pandas as pd

# TODO: emberi header-ök

def string_to_dict_list(input_string):
    try:
        data_list = json.loads(input_string)
        return data_list
    except json.JSONDecodeError:
        return None
    
def polygon_dict_to_dataframe(bar_dict: dict) -> pd.DataFrame:
    pass
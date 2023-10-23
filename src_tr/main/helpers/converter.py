import json

def string_to_dict_list(input_string):
    try:
        data_list = json.loads(input_string)
        return data_list
    except json.JSONDecodeError:
        return None
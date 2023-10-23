import json

def string_to_dict_list(input_string):
    try:
        data_list = json.loads(input_string)
        return data_list
    except json.JSONDecodeError:
        return None

# Example usage:
input_string = '[{"T":"b","S":"AAPL","o":171.3,"h":171.51,"l":171.24,"c":171.51,"v":2841,"t":"2023-10-23T14:13:00Z","n":40,"vw":171.367034}]'
result = string_to_dict_list(input_string)
print(result)

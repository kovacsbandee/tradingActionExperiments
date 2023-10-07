import pandas as pd

# Your list of dictionaries
data_list = [{"T":"b",
              "S":"AAPL",
              "o":171.68,
              "h":171.68,
              "l":171.585,
              "c":171.605,
              "v":1961,
              "t":"2023-10-03T18:16:00Z",
              "n":22,
              "vw":171.618957}, {"T":"b",
              "S":"AAPL",
              "o":171.68,
              "h":171.68,
              "l":171.585,
              "c":171.605,
              "v":1961,
              "t":"2023-10-03T18:16:00Z",
              "n":22,
              "vw":171.618957},{"T":"b",
              "S":"AAPL",
              "o":171.68,
              "h":171.68,
              "l":171.585,
              "c":171.605,
              "v":1961,
              "t":"2023-10-03T18:16:00Z",
              "n":22,
              "vw":171.618957}]

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(data_list)

# Print the DataFrame
print(df)

current_data_window = {
        'AAPL': [{"T":"b",
                "S":"AAPL",
                "o":171.68,
                "h":171.68,
                "l":171.585,
                "c":171.605,
                "v":1961,
                "t":"2023-10-03T18:16:00Z",
                "n":22,
                "vw":171.618957}, {"T":"b",
                "S":"AAPL",
                "o":171.68,
                "h":171.68,
                "l":171.585,
                "c":171.605,
                "v":1961,
                "t":"2023-10-03T18:16:00Z",
                "n":22,
                "vw":171.618957}, {"T":"b",
                "S":"AAPL",
                "o":171.68,
                "h":171.68,
                "l":171.585,
                "c":171.605,
                "v":1961,
                "t":"2023-10-03T18:16:00Z",
                "n":22,
                "vw":171.618957}],
        'MSFT': [],
        'TSLA': []
    }

st = [s for s in current_data_window.keys()]

for s in st:
    print(pd.DataFrame(current_data_window[s]))
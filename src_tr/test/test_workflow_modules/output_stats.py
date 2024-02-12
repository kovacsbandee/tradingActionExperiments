import os
import csv
import json
from datetime import datetime
from config import config

def _convert_to_float(symbol_daily_output_list):
    converted_list = []
    for e in symbol_daily_output_list:
        e['t'] = datetime.strptime(e['t'], "%Y-%m-%d %H:%M:%S%z")
        e['o'] = float(e['o'])
        e['c'] = float(e['c'])
        e['h'] = float(e['h'])
        e['l'] = float(e['l'])
        e['v'] = float(e['v'])
        e['n'] = float(e['n'])
        e['current_capital'] = float(e['current_capital']) if e['current_capital'] != '' else None
        e['rsi'] = float(e['rsi']) if e['rsi'] != '' else None
        e['open_small_indicator'] = float(e['open_small_indicator']) if e['open_small_indicator'] != '' else None
        e['open_big_indicator'] = float(e['open_big_indicator']) if e['open_big_indicator'] != '' else None
        e['open_norm'] = float(e['open_norm']) if e['open_norm'] != '' else None
        e['gain_loss'] = float(e['gain_loss']) if e['gain_loss'] != '' else None
        e['gain'] = float(e['gain']) if e['gain'] != '' else None
        e['loss'] = float(e['loss']) if e['loss'] != '' else None
        e['avg_gain'] = float(e['avg_gain']) if e['avg_gain'] != '' else None
        e['avg_loss'] = float(e['avg_loss']) if e['avg_loss'] != '' else None
        e['current_range'] = float(e['current_range']) if e['current_range'] != '' else None
        e['atr_short'] = float(e['atr_short']) if e['atr_short'] != '' else None
        converted_list.append(e)
    return converted_list

def _calculate_symbol_stats(symbol_data_list):
    symbol = symbol_data_list[0]["S"]
    capital_ts_dict_list = [{"current_capital" : i["current_capital"], "timestamp" : i['t']} for i in symbol_data_list]
    max_cash = 0
    max_cash_ts = None
    for i in capital_ts_dict_list:
        curr_cap = i["current_capital"]
        curr_ts = i["timestamp"]
        if curr_cap is not None and curr_ts is not None and curr_cap > max_cash:
            max_cash = curr_cap
            max_cash_ts = curr_ts
    
    end_cash = None
    capital_list_reverse = [i["current_capital"] for i in capital_ts_dict_list if i['current_capital'] is not None][::-1]
    for c in capital_list_reverse:
        if c is not None and c != 0:
            end_cash = c
            break
        else:
            continue
    market_buy_count = len([i["trading_action"] for i in symbol_data_list if i["trading_action"] == "buy_next_long_position"])
    
    longs = []
    counter = 0
    positions = [i["position"] for i in symbol_data_list]
    for i in range(len(positions)):
        if positions[i] == "long":
            counter += 1
        elif counter > 0 and positions[i] != "long":
            longs.append(counter)
            counter = 0
    avg_long_position_length = round(sum(longs) / len(longs), 2)
    long_position_length_mode = max(set(longs), key=longs.count)
    long_position_length_max = max(longs)
    long_position_length_min = min(longs)
    
    position_close_count = len([i["trading_action"] for i in symbol_data_list if i["trading_action"] == "sell_previous_long_position"])
    stop_loss_count = len([i["stop_loss_out_signal"] for i in symbol_data_list if i["stop_loss_out_signal"] == "stop_loss_long"])
    stop_loss_percentage = round(stop_loss_count/position_close_count*100, 2)
    
    rsi_avg = sum([i["rsi"] for i in symbol_data_list if i["rsi"] is not None]) / len(symbol_data_list)
    
    return {
        "symbol" : symbol,
        "max_cash" : max_cash,
        "max_cash_ts" : max_cash_ts.strftime("%Y-%m-%d %H:%M:%S%z"),
        "end_cash" : end_cash,
        "market_buy_count" : market_buy_count,
        "avg_long_position_length" : avg_long_position_length,
        "long_position_length_mode" : long_position_length_mode,
        "long_position_length_max" : long_position_length_max,
        "long_position_length_min" : long_position_length_min,
        "position_close_count" : position_close_count,
        "stop_loss_percentage" : stop_loss_percentage,
        "rsi_avg" : rsi_avg
    }

def create_stats_by_symbol(input_folder):
    input_path = os.path.join(config['db_path'], input_folder, "daily_files/csvs")
    csvs = os.listdir(input_path)
    csvs.sort()
    stats_by_symbol = []
    for filename in csvs:
        with open(file=f"{input_path}/{filename}") as symbol_output:
            symbol_daily_output_list = [
                {k : v for k, v in row.items()}
                for row in csv.DictReader(symbol_output, skipinitialspace=True)
            ]
            converted = _convert_to_float(symbol_daily_output_list)
            calculated_stats = _calculate_symbol_stats(converted)
            stats_by_symbol.append(calculated_stats)
    return stats_by_symbol

def create_overall_stats(stat_list, cash_by_symbol):
    result_dict = dict()
    starting_total_cash = len(stat_list) * cash_by_symbol
    result_dict["starting_total_cash"] = starting_total_cash
    max_cash_sum = sum([s["max_cash"] for s in stat_list])
    max_cash_ts_list = [i["max_cash_ts"] for i in stat_list]
    end_cash_sum = sum([s["end_cash"] for s in stat_list])
    symbols_with_profit = len([i for i in stat_list if i["end_cash"] > cash_by_symbol])
    symbols_with_loss = len([i for i in stat_list if i["end_cash"] < cash_by_symbol])
    profit_loss_ratio = f"{symbols_with_profit}:{symbols_with_loss}"
    
    result_dict["max_profit_sum"] = round(max_cash_sum - starting_total_cash, 4)
    result_dict["max_profit_pct"] = round(max_cash_sum / starting_total_cash * 100, 4)
    result_dict["max_cash_ts_list"] = max_cash_ts_list
    result_dict["end_profit_sum"] = round(end_cash_sum - starting_total_cash, 4)
    result_dict["end_profit_pct"] = round(end_cash_sum / starting_total_cash * 100, 4)
    result_dict["profit_loss_ratio"] = profit_loss_ratio
    return result_dict

def compose_output(foldername, overall_stats, stats_by_symbol, symbols_with_loss):
    return {
        "foldername" : foldername,
        "overall_stats" : overall_stats,
        "stats_by_symbol" : stats_by_symbol,
        "symbols_with_loss" : symbols_with_loss
    }

#folders = os.listdir(f"{config['db_path']}/SimpleAVG_timelimit4hours_origscanner_sp500only_trading_day_2023_03_16")
#for folder in folders:
batch_foldername = "MACD_26_12_9_trading_day_2023_03_06"
cash_by_symbol = 10000
stat_list = create_stats_by_symbol(input_folder=batch_foldername)
overall_stats = create_overall_stats(stat_list=stat_list,
                                    cash_by_symbol=cash_by_symbol)

symbols_with_loss = [{k : v for k, v in i.items()} for i in stat_list if i["end_cash"] < cash_by_symbol]

output_dict = compose_output(foldername=batch_foldername,
                            overall_stats=overall_stats,
                            stats_by_symbol=stat_list,
                            symbols_with_loss=symbols_with_loss)

with open(f"{config['db_path']}/output_stats/json/{batch_foldername}.json", "w") as file:
    json.dump(output_dict, file)
    

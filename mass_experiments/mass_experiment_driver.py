import pandas as pd
from mass_experiment import get_all_file_w_paths, run_parallel_strategy_operations
from plots.plots import create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments

PROJ_PATH = 'F:/tradingActionExperiments'
DB_PATH = f'F:/tradingActionExperiments_database/database_day_stock'

short_ma = 5
long_ma = 12
experiment_description = f'test_w_combined_strategy_ma{short_ma}_ma{long_ma}'

files = get_all_file_w_paths()
res_df = run_parallel_strategy_operations(all_csvs=files, exp_desc=experiment_description)
plots = res_df[res_df['final_capital'] > 3150]
for i, row in plots.iterrows():
    d = row['date'].replace('-', '_')
    s = row['sticker']
    print(d,s)
    df = pd.read_csv(f'{DB_PATH}/stock_prices_for_{d}/csvs/{s}_{experiment_description}.csv')
    create_candle_stick_chart_w_indicators_for_trendscalping_for_mass_experiments(plot_df=df,
                                                             sticker_name=s,
                                                             plot_name=f'{experiment_description}_with_positions_{d}',
                                                             indicators=['current_capital',
                                                                         f'close_ma{short_ma}',
                                                                         f'close_ma{short_ma}_grad',
                                                                         f'close_ma{long_ma}',
                                                                         f'close_ma{long_ma}_grad'])
results = pd.read_csv(f'{PROJ_PATH}/data_store/results/{experiment_description}.csv')
test = results[results['sticker'].isin(results[results['final_capital'] > 3050]['sticker'].unique())]
test = test[test.final_capital>0][['date','sticker', 'final_capital']].copy()
test.sort_values(by=['sticker', 'date'], inplace=True)
test.to_csv('test.csv')
t=test[test.final_capital>0].groupby(by='sticker').mean()
t.to_csv('t.csv')
param_dict = {
    # "paper_trading_26-12-9_closeRSI70-10_noRSIentry" : {
    #         "scanner_params" : {
    #             "windows" : {
    #                 "short" : 12,
    #                 "long" : 26,
    #                 "signal" : 9
    #             }
    #         },
    #         "algo_params" : {
    #             "entry_signal" : "MACD",
    #             "rsi_length" : 12,
    #             "entry_rsi" : {
    #                 "overbought" : 60,
    #                 "oversold" : 20
    #             },
    #             "entry_windows" : {
    #                 "short" : 12,
    #                 "long" : 26,
    #                 "signal" : 9
    #             },
    #             "entry_weighted" : True,
    #             "close_signal" : "AVG",
    #             "close_rsi" : {
    #                 "overbought" : 70,
    #                 "oversold" : 10
    #             },
    #             "close_window" : 5,
    #             "close_weighted" : True
    #         }
    #     }
#     ,
#     "eMACD_cAVG_eRSI30_cRSI70" : {
#             "scanner_params" : {
#                 "windows" : {
#                     "short" : 12,
#                     "long" : 26,
#                     "signal" : 9
#                 }
#             },
#             "algo_params" : {
#                 "entry_signal" : "MACD",
#                 "rsi_length" : 12,
#                 "entry_rsi" : {
#                     "overbought" : 70,
#                     "oversold" : 30
#                 },
#                 "entry_windows" : {
#                     "short" : 12,
#                     "long" : 26,
#                     "signal" : 9
#                 },
#                 "entry_weighted" : True,
#                 "close_signal" : "AVG",
#                 "close_rsi" : {
#                     "overbought" : 70,
#                     "oversold" : 10
#                 },
#                 "close_window" : 5,
#                 "close_weighted" : True
#             }
#         },
#     "eMACD_cATR_eRSI30_cRSI70" : {
#             "scanner_params" : {
#                 "windows" : {
#                     "short" : 12,
#                     "long" : 26,
#                     "signal" : 9
#                 }
#             },
#             "algo_params" : {
#                 "entry_signal" : "MACD",
#                 "rsi_length" : 12,
#                 "entry_rsi" : {
#                     "overbought" : 70,
#                     "oversold" : 30
#                 },
#                 "entry_windows" : {
#                     "short" : 12,
#                     "long" : 26,
#                     "signal" : 9
#                 },
#                 "entry_weighted" : True,
#                 "close_signal" : "ATR",
#                 "close_rsi" : {
#                     "overbought" : 70,
#                     "oversold" : 10
#                 },
#                 "close_window" : 5,
#                 "close_weighted" : True
#             }
#         }
# }
    "E-RSI_10-MACD16_6_3--C-AVG_5-RSI_70": {
        "scanner_params": {
            "windows": {
                "short": 12,
                "long": 26,
                "signal": 9
            }
        },
        "algo_params": {
            "entry_signal": "MACD",
            "rsi_length": 12,
            "entry_rsi": {
                "overbought": 70,
                "oversold": 10
            },
            "entry_windows": {
                "short": 6,
                "long": 16,
                "signal": 3
            },
            "entry_weighted": True,
            "close_signal": "AVG",
            "close_rsi": {
                "overbought": 70,
                "oversold": 10
            },
            "close_window": 5,
            "close_weighted": True
        }
    },
    "E-MACD16_6_3--C-AVG_5-RSI_70": {
        "scanner_params": {
            "windows": {
                "short": 12,
                "long": 26,
                "signal": 9
            }
        },
        "algo_params": {
            "entry_signal": "MACD",
            "rsi_length": 12,
            "entry_rsi": None,
            "entry_windows": {
                "short": 6,
                "long": 16,
                "signal": 3
            },
            "entry_weighted": True,
            "close_signal": "AVG",
            "close_rsi": {
                "overbought": 70,
                "oversold": 10
            },
            "close_window": 5,
            "close_weighted": True
        }
    },
    "E-RSI_10-MACD16_6_3--C-AVG_5": {
        "scanner_params": {
            "windows": {
                "short": 12,
                "long": 26,
                "signal": 9
            }
        },
        "algo_params": {
            "entry_signal": "MACD",
            "rsi_length": 12,
            "entry_rsi": {
                "overbought": 70,
                "oversold": 10
            },
            "entry_windows": {
                "short": 6,
                "long": 16,
                "signal": 3
            },
            "entry_weighted": True,
            "close_signal": "AVG",
            "close_rsi": None,
            "close_window": 5,
            "close_weighted": True
        }
    },
    "E-MACD16_6_3--C-AVG_5": {
        "scanner_params": {
            "windows": {
                "short": 12,
                "long": 26,
                "signal": 9
            }
        },
        "algo_params": {
            "entry_signal": "MACD",
            "rsi_length": 12,
            "entry_rsi": None,
            "entry_windows": {
                "short": 6,
                "long": 16,
                "signal": 3
            },
            "entry_weighted": True,
            "close_signal": "AVG",
            "close_rsi": None,
            "close_window": 5,
            "close_weighted": True
        }
    }
}
#NOTE: eredeti Kovi-féle
    #"randomId_20240214" : {
    #        "scanner_params" : {
    #            "windows" : {
    #                "short" : 12,
    #                "long" : 26,
    #                "signal" : 9
    #            }
    #        },
    #        "algo_params" : {
    #            "entry_signal" : "default",
    #            "rsi_length" : 12,
    #            "entry_rsi" : {
    #                "overbought" : 70,
    #                "oversold" : 30
    #            },
    #            "entry_windows" : {
    #                "short" : 4,
    #                "long" : 10,
    #                "epsilon" : 0.0015
    #            },
    #            "entry_weighted" : False,
    #            "close_signal" : "AVG",
    #            "close_rsi" : {
    #                "overbought" : 70,
    #                "oversold" : 30
    #            },
    #            "close_window" : 5,
    #            "close_weighted" : True
    #        }
    #    }
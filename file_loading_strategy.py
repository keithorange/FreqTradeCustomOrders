from datetime import datetime
import json
import time
from typing import Any, Dict, Optional
from freqtrade.persistence.trade_model import Order, Trade
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import numpy as np
import pandas_ta as pta
from custom_order_form_handler import OrderStatus, StrategyDataHandler, ACTIVE_ORDER_STATUSES_VALUES
from entry_conditions import price_crosses_upward, price_reverses_up, price_under
from dateutil import parser
import threading
import logging


class FileLoadingStrategy(IStrategy):
    """
    Strategy class that reads order details from a file and sets strategy variables accordingly.
    """

    # Default parameters
    stoploss = -1.0

    def __init__(self, config) -> None:
        """
        Initialize the strategy with the given configuration.
        """
        super().__init__(config)
        self.strategy_name = self.__class__.__name__
        self.order_handler = StrategyDataHandler(
            strategy_name=self.strategy_name)
        self.monitoring_initialized = False
        
    def input_strategy_data(self, pair: str):
        """
        Placeholder method for handling argument input from file data handler.
        Implementation will vary based on specific strategy.
        """
        raise NotImplementedError

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        """
        Placeholder method for setting entry signal.
        Implementation will vary based on specific strategy.
        """
        raise NotImplementedError

    def does_pair_have_data(self, pair) -> bool:
        data = self.order_handler.read_strategy_data()
        return pair in data

    def get_pair_data(self, pair) -> Dict[str, Any]:
        if not self.does_pair_have_data(pair):
            raise LookupError(f"{pair} doesn't have data yet!")
        return self.order_handler.read_strategy_data()[pair]

    def does_pair_have_active_order(self, pair) -> bool:
        if self.does_pair_have_data(pair):
            data = self.get_pair_data(pair)
            if data['status'] in ACTIVE_ORDER_STATUSES_VALUES:
                return True
        return False

    def get_dfile_arg(self, pair, key):
        data = self.get_pair_data(pair)
        if key in data:
            return data[key]
        return None

    def set_dfile_arg(self, pair, key, value):
        data = self.order_handler.read_strategy_data()
        if not self.does_pair_have_data(pair):
            data[pair] = {}
        data[pair][key] = value
        

        self.order_handler.save_strategy_data(data)

    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        if not self.monitoring_initialized:
            self.start_monitoring()
            self.monitoring_initialized = True

    def start_monitoring(self):
        monitor_thread = threading.Thread(target=self.monitor_entry_conditions)
        monitor_thread.start()

    # Ensure last_prices is a list in monitor_entry_conditions


    def monitor_entry_conditions(self):
        while True:
            strategy_data = self.order_handler.read_strategy_data()

            for pair, data in strategy_data.items():
                if data['status'] == OrderStatus.WAITING.value:
                    condition_type = data['entry_condition']
                    entry_condition_timeout = data['entry_condition_timeout']
                    entry_condition_price = data.get('entry_condition_price')
                    threshold_pct = data.get('threshold_pct', 0.15)
                    ma_type = data.get('ma_type', 'EMA')
                    period = data.get('period', 14)

                    # USING EMA/HMA NOT CLOSE!
                    last_prices = data.get('prices', [])
                    
                    # Check if prices is a LIST filled with price data!
                    if not isinstance(last_prices, list) or len(last_prices) < 10 or not all(isinstance(price, (int, float)) for price in last_prices):
                        logging.error(f"Invalid data type or insufficient data in last_prices: {type(last_prices)} for {pair}")
                        continue


                    # Check the condition
                    if condition_type == 'PriceReversesUpCondition':
                        is_satisfied = price_reverses_up(
                            last_prices=last_prices,
                            period=period,
                            threshold_pct=threshold_pct,
                        )
                    elif condition_type == 'PriceCrossesUpwardCondition':
                        if not entry_condition_price:
                            logging.error(f"Missing entry_condition_price for pair {pair}: {data}")
                            continue
                        is_satisfied = price_crosses_upward(
                            entry_condition_price,
                            last_prices=last_prices
                        )
                    elif condition_type == 'PriceUnderCondition':
                        if not entry_condition_price:
                            logging.error(f"Missing entry_condition_price for pair {pair}: {data}")
                            continue
                        is_satisfied = price_under(
                            entry_condition_price,
                            last_prices=last_prices
                        )
                    else:
                        logging.error(f"Invalid condition type for pair {pair}: {data}")
                        continue
                    
                    if is_satisfied:
                        data['status'] = OrderStatus.PENDING.value

                    if entry_condition_timeout and datetime.now() >= parser.parse(entry_condition_timeout):
                        data['status'] = OrderStatus.CANCELED.value

                    self.order_handler.update_strategy_data(pair, data)

                # SLEEP 2x per min!
            time.sleep(31)



    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        last_candle = dataframe.iloc[-1].squeeze()
        price = last_candle['close']

        
        strategy_data = self.order_handler.read_strategy_data()

        # only enter if PENDING pair!
        if pair in strategy_data and strategy_data[pair]['status'] == OrderStatus.PENDING.value:
            # Enter trade freqtrade bot
            self.set_entry_signal(pair, dataframe, strategy_data[pair])
            
            # write variabels to saved log
            strategy_data[pair]['status'] = OrderStatus.HOLDING.value
            strategy_data[pair]['entry_price'] = price
            
            # write to file
            self.order_handler.update_strategy_data(pair, strategy_data[pair])
            
        else:
            self.set_no_entry(dataframe)

        return dataframe


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def set_no_entry(self, dataframe):
        dataframe.loc[dataframe.index[-1],
                      ['enter_long', 'enter_tag']] = (0, "no_enter")

    def set_no_exit(self, dataframe):
        dataframe.loc[dataframe.index[-1],
                      ['exit_long', 'exit_tag']] = (0, "no_exit")

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float, proposed_stake: float, min_stake: Optional[float], max_stake: float, leverage: float, entry_tag: Optional[str], side: str, **kwargs) -> float:
        default_stake = 10  # $10 if no stake is found
        try:
            return self.get_dfile_arg(pair, 'stake_amount')
        except ValueError as e:
            print(f"Error: {e}")
        return default_stake

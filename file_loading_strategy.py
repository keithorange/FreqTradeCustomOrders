import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from pandas import DataFrame
from custom_order_form_handler import OrderStatus, StrategyDataHandler
from freqtrade.strategy.interface import IStrategy



class FileLoadingStrategy(IStrategy):
    
    # default parameters
    stoploss = -1.0

    def __init__(self, config) -> None:
        super().__init__(config)
        
        strategy_name = self.__class__.__name__
        self.strategy_name = strategy_name
        self.order_handler = StrategyDataHandler(strategy_name=strategy_name)
      

        
    # HANDLES ARGUMENT INPUTTING FROM FILE DATA HANDLER
    def input_strategy_data(self, pair: str):
        # Implementation will vary based on strategy
        raise NotImplementedError
    
    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        # Implementation will vary based on strategy
        raise NotImplementedError

    
    def get_file_data(self, pair) -> (Dict[str, Any], OrderStatus): # type: ignore
        #print(f"self.args = {self.args}")
        if pair in self.args:
            d = self.args[pair] 
            #print(f"\n\tget_file_data: {d}\n")
            return d['data'], d['status']
        else:
            #print(f"\n\tget_file_data: {pair} not in {self.args}\n")
            return {}, None
        

    def get_dfile_arg(self, pair, key, ):
        data, status = self.get_file_data(pair)
        #print(f" Pair: {pair} Key: {key} Data: {data} Status: {status}")
        
        if key in data:    
            return data[key]
        else:
            print(f'ValueError(Key {key} not found in {data}')
            return None
    

    def set_dfile_arg(self, pair, key, value):
        # get fresh args
        self.args = self.order_handler.read_strategy_data()

        # Check if the pair exists in self.args
        if pair not in self.args:
            self.args[pair] = {"data": {}}

        # Check if the "data" key exists for the pair
        if "data" not in self.args[pair]:
            self.args[pair]["data"] = {}

        # Set the value for the given key
        self.args[pair]["data"][key] = value

        # Save the updated strategy data
        #print(f'SAVING STRATEGY DATA: {self.args[pair]["data"]}')
        self.order_handler.save_strategy_data(self.args)



    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        """
        Called at the start of the bot iteration (one loop).
        Used to read order details from a file and set strategy variables accordingly.
        """
        # if self.config['runmode'].value in ('live', 'dry_run'):
            
        #     # Read and parse the JSON content
            
        self.args = self.order_handler.read_strategy_data()
                       

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        strategy_data = self.order_handler.read_strategy_data()

        # # log
        # print(f"Strategy Data: {strategy_data}")
        # if pair in strategy_data:
        #     print(f"Strategy Data for {pair}: {strategy_data[pair]}")
        # else:
        #     print(f"Strategy Data for {pair} not found")

        # Pending buy order , place order
        if pair in strategy_data and strategy_data[pair]['status'] == OrderStatus.PENDING.value:
            self.set_entry_signal(pair, dataframe, strategy_data[pair]['data'])
            self.order_handler.update_strategy_data(pair, strategy_data[pair]['data'], OrderStatus.HOLDING)
        else:
            self.set_no_entry(dataframe)
            
        return dataframe

    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,rate: float, time_in_force: str, exit_reason: str,current_time: datetime, **kwargs) -> bool:
        # if exit_reason not in ['roi', 'stop_loss', 'emergency_exit']:
        #     return False

        # Write Flag to file
        strategy_data = self.order_handler.read_strategy_data()
        self.order_handler.update_strategy_data(pair, strategy_data[pair]['data'], OrderStatus.EXITED)
        return True
    
    # No customization
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

    # Load $$$ stake amount from file
    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,proposed_stake: float, min_stake: Optional[float], max_stake: float,leverage: float, entry_tag: Optional[str], side: str,**kwargs) -> float:

        default_stake = 10 # 10$ if no stake is found
        try:
            return self.get_dfile_arg(pair, 'stake_amount')

        except ValueError as e:
            print(f"Error: {e}")

        return default_stake
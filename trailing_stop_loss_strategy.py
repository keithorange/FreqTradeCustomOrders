import json
import os
from datetime import datetime
import time
from typing import Optional
from file_loading_strategy import FileLoadingStrategy
from freqtrade.strategy.interface import IStrategy
from freqtrade.persistence import Trade
# additional imports required
from datetime import datetime
import json
import os
from typing import Any, Optional

from pandas import DataFrame
from typing import Dict
from custom_order_form_handler import OrderStatus
from file_loading_strategy import FileLoadingStrategy
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.strategy_helper import stoploss_from_open
from freqtrade.persistence import Trade


class TrailingStopLossStrategy(FileLoadingStrategy):
    use_custom_stoploss = True
    

    stoploss = -1.0  # default off

    # not pair-specific
    # trailing_stop = True
    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime, current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> Optional[float]:
        
    #     # set default trailing stop loss
    #     try:
    #         trailing_stop_loss_pct = self.get_file_arg(
    #             pair, 'trailing_stop_loss_pct')
    #         if self.stoploss != -trailing_stop_loss_pct:
    #             self.stoploss = -trailing_stop_loss_pct

    #     except Exception as e:
    #         print(f"Error: populate_indicators: {e}")
        

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime, current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> Optional[float]:
        """
        Custom stoploss logic based on pair-specific data.
        """
        # Retrieve pair specific trailing stop loss percentage, use default if not found
        try:
            trailing_stop_loss_pct = self.get_file_arg(pair, 'trailing_stop_loss_pct')

            print(f"trailing_stop_loss_pct: {trailing_stop_loss_pct}")
            return -trailing_stop_loss_pct
        except ValueError as e:
            print(f"Error: get_file_arg in custom_stoploss: {e}")
            return None

    def input_strategy_data(self, pair: str):
        trailing_stop_loss_pct = float(
            input("Specify your trailing stop loss as a percentage (e.g., enter '1' for a 1% trailing stop loss): ")) 
        
        stake_amount = float(input("Enter the amount you want to invest in this trade (default is $10 if left blank): "))

        order_data = {"trailing_stop_loss_pct": trailing_stop_loss_pct,
                      "stake_amount": stake_amount}

        print("\nPlease review your order details:")
        print(json.dumps(order_data, indent=4))
        confirmation = input(
            "Type 'Y' to confirm and submit your order, anything else to cancel: ").upper()

        if confirmation == 'Y':
            self.order_handler.update_strategy_data(
                pair, order_data, OrderStatus.PENDING)
            print("\nSubmitted order!")
            print(json.dumps(order_data, indent=4))
        else:
            print("\nCancelled placing order!")

        time.sleep(3)

        self.order_handler.update_strategy_data(
            pair, order_data, OrderStatus.PENDING)
        
        

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        try:
            trailing_stop_loss_pct = self.get_file_arg(pair, "trailing_stop_loss_pct")
            dataframe.loc[dataframe.index[-1], ['enter_long', 'enter_tag']] = (1, f"TSL_user_enter_(tsl={trailing_stop_loss_pct}")
        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None
    


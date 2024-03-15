# additional imports required
from datetime import datetime
import json
import os
from typing import Any, Optional, Dict

from pandas import DataFrame

from custom_order_form_handler import OrderStatus
from file_loading_strategy import FileLoadingStrategy
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.strategy_helper import stoploss_from_open
from freqtrade.persistence import Trade

"""

Your JSON file (pair_orders.json) should then be structured as follows:

json

{
    "BTC/USDT": {
        "stop_loss_pct": 0.03
    },
    "ETH/USDT": {
        "stop_loss_pct": 0.04
    }
    // Add more pairs as needed
}


"""


class StopLossStrategy(FileLoadingStrategy):

    use_custom_stoploss = True
    
    trailing_stop = False
    
    stoploss = -1.0  # default off
    
    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime, current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> Optional[float]:

    #     try:
    #         # Also setup stoploss from file data
    #         stop_loss_pct = self.get_file_arg(pair, 'stop_loss_pct')
    #         if self.stoploss != -stop_loss_pct:
    #             self.stoploss = -stop_loss_pct

    #     except Exception as e:
    #         print(f"Error: populate_indicators: {e}")

    
    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool,
                        **kwargs) -> Optional[float]:
        """
        Custom stoploss logic, returning the new distance relative to current_rate (as ratio).
        e.g. returning -0.05 would create a stoploss 5% below current_rate.
        The custom stoploss can never be below self.stoploss, which serves as a hard maximum loss.

        For full documentation please go to https://www.freqtrade.io/en/latest/strategy-advanced/

        When not implemented by a strategy, returns the initial stoploss value.
        Only called when use_custom_stoploss is set to True.

        :param pair: Pair that's currently analyzed
        :param trade: trade object.
        :param current_time: datetime object, containing the current datetime
        :param current_rate: Rate, calculated based on pricing settings in exit_pricing.
        :param current_profit: Current profit (as ratio), calculated based on current_rate.
        :param after_fill: True if the stoploss is called after the order was filled.
        :param **kwargs: Ensure to keep this here so updates to this won't break your strategy.
        :return float: New stoploss value, relative to the current_rate
        """
        
        stop_loss_pct = self.get_file_arg(pair, 'stop_loss_pct')

        
        # Calculate stoploss relative to open price (no trailing)
        return -max(stoploss_from_open(
            -stop_loss_pct, current_profit, is_short=trade.is_short, leverage=trade.leverage), stop_loss_pct)

    def input_strategy_data(self, pair: str):
        stop_loss_pct = float(
            input("Enter stop_loss_pct (NOTE: 1 == -1% SL): ")) / 100
        stake_amount = float(input("Enter stake amount (default is $10):  "))

        self.order_handler.update_strategy_data(
            pair, {"stop_loss_pct": stop_loss_pct,
                   "stake_amount": stake_amount}, OrderStatus.PENDING)

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        try:
            stop_loss_pct = self.get_file_arg(pair, 'stop_loss_pct')
            dataframe.loc[dataframe.index[-1], ['enter_long',
                                                'enter_tag']] = (1, f"SL_user_enter_{stop_loss_pct}")

        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None
    
from datetime import datetime
import json
import time
from typing import Optional
from file_loading_strategy import FileLoadingStrategy
from freqtrade.strategy.strategy_helper import stoploss_from_open
from freqtrade.persistence import Trade

# additional imports required
from datetime import datetime
from typing import Any, Optional

from pandas import DataFrame
from typing import Dict
from custom_order_form_handler import OrderStatus
from file_loading_strategy import FileLoadingStrategy
from freqtrade.persistence import Trade

class TPActivatingTSLwithSLStrategy(FileLoadingStrategy):

    # use default variable, no callback needed (self.custom_stoploss)
    use_custom_stoploss = True
    stoploss = -1.0 #default off
    
    
    # DOESN'T WORK FOR PAIR-SPECIFIC STOP-LOSS  
    # trailing_stop = True
    # trailing_only_offset_is_reached = True
    # trailing_stop_positive = 0.99
    # trailing_stop_positive_offset = 1.0 

    # def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> Optional[float]:
    #     try:
            
    #         hard_stop_loss =self.get_file_arg(pair, 'hard_stop_loss')
    #         trailing_stop_loss =self.get_file_arg(pair, 'trailing_stop_loss')
    #         profit_activating_tsl =self.get_file_arg(pair, 'profit_activating_tsl')
            
    #         self.stoploss = -hard_stop_loss
                
    #         self.trailing_stop_positive_offset = profit_activating_tsl
            
    #         self.trailing_stop_positive = trailing_stop_loss
            
    #         print(f"""
    #         (custom_stoploss)DEBUGGING
            
    #         hard_stop_loss: {hard_stop_loss}
    #         trailing_stop_loss: {trailing_stop_loss}
    #         profit_activating_tsl: {profit_activating_tsl}
            
            
    #               """)
            
    #     except Exception as e:
    #         print(f"Error: populate_indicators: {e}")
        
    #     # return nothing (we update self. ourselves)
        
        

        # return nothing, no exit only update stoploss

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> Optional[float]:
        try:

            trailing_stop_loss = self.get_file_arg(pair, 'trailing_stop_loss')
            hard_stop_loss = self.get_file_arg(pair, 'hard_stop_loss')
            profit_activating_tsl = self.get_file_arg(pair, 'profit_activating_tsl')
            take_profit_hit = self.get_dfile_arg(pair, 'take_profit_hit')
            
             # Calculating the percentage difference between the current rate and the open trade rate
            percentage_difference = ((current_rate - trade.open_rate) / trade.open_rate) * 100

            print(f"""
                TPActivatingTSLwithSLStrategy
                    current_rate: {current_rate}
                    open_rate: {trade.open_rate}
                    percentage_difference: {percentage_difference}%
                    profit_activating_tsl: {profit_activating_tsl}
                    
                    Is percentage_difference < profit_activating_tsl? {percentage_difference < profit_activating_tsl}
                """)

            # Check if the percentage difference is below the threshold to activate trailing stop loss
            if not take_profit_hit or percentage_difference < profit_activating_tsl:
                print(f"""
                      current_profit: {current_profit}
                      profit_activating_tsl: {profit_activating_tsl}
                      
                      hard_stop_loss: {hard_stop_loss}
                      
                      stoploss_from_open(-hard_stop_loss, current_profit, is_short=trade.is_short, leverage=trade.leverage): {stoploss_from_open(-hard_stop_loss, current_profit, is_short=trade.is_short, leverage=trade.leverage)}
                      """)
                # at start or Negative profit, set hard stoploss as default
                return -stoploss_from_open(-hard_stop_loss, current_profit, is_short=trade.is_short, leverage=trade.leverage)
        
            else: # HIT! turn on TSL
                self.set_file_arg(pair, 'take_profit_hit', True)
                return -trailing_stop_loss
            
        except ValueError as e:
            print(f"Error: get_file_arg in custom_stoploss: {e}")
            return None

        

    def input_strategy_data(self, pair: str):

        
        hard_stop_loss = float(
            input("Set your hard (initial and static) stop loss as a percentage (e.g., '1' for a 1% hard stop loss): ")) 

        trailing_stop_loss = float(
            input("Define your trailing stop loss percentage (e.g., '1' for a 1% trailing stop loss): ")) 
  

        profit_activating_tsl = float(
            input("Enter the percentage gain at which to activate the trailing stop loss (e.g., '1' for activation at 1% profit): "))


        stake_amount = float(input("Enter the amount you wish to invest in this trade (leave blank for $10 default): "))

        order_data = {
            "profit_activating_tsl": profit_activating_tsl,
            "take_profit_hit": False, 
            "trailing_stop_loss": trailing_stop_loss,
            "hard_stop_loss": hard_stop_loss,
            "stake_amount": stake_amount,
        }

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


        self.order_handler.update_strategy_data(pair, order_data, OrderStatus.PENDING)

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        
        try:
            hard_stop_loss = self.get_file_arg(pair, 'hard_stop_loss')
            trailing_stop_loss = self.get_file_arg(pair, 'trailing_stop_loss')
            profit_activating_tsl = self.get_file_arg(
                pair, 'profit_activating_tsl')
            dataframe.loc[dataframe.index[-1], ['enter_long',
                                                'enter_tag']] = (1, f"TP&TSL&SL_user_enter_(TP={profit_activating_tsl}, TSL={trailing_stop_loss}, SL={hard_stop_loss})")

        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None

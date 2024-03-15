from datetime import datetime
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

class TPActivatingTSLwithInitialTSLStrategy(FileLoadingStrategy):

    """
    Similar to TPActivatingTSLwithSLStrategy but uses TSL initially rather than SL. Once TP hit, "tight" TSL is activated.
    """

    # use default variable, no callback needed (self.custom_stoploss)
    use_custom_stoploss = True
    stoploss = -1.0 #default off
    
 


    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float, after_fill: bool, **kwargs) -> Optional[float]:
        try:

            tight_trailing_stop_loss = self.get_dfile_arg(
                pair, 'tight_trailing_stop_loss')
            loose_trailing_stop_loss = self.get_dfile_arg(
                pair, 'loose_trailing_stop_loss')
            profit_activating_tsl = self.get_dfile_arg(pair, 'profit_activating_tsl')
             # Calculating the percentage difference between the current rate and the open trade rate
            percentage_difference = ((current_rate - trade.open_rate) / trade.open_rate) * 100

            # print(f"""
            #     TPActivatingTSLwithInitialTSLStrategy
            #         current_rate: {current_rate}
            #         open_rate: {trade.open_rate}
            #         percentage_difference: {percentage_difference}%
            #         profit_activating_tsl: {profit_activating_tsl}
                    
            #         Is percentage_difference < profit_activating_tsl? {percentage_difference < profit_activating_tsl}
            #     """)

            # Check if the percentage difference is below the threshold to activate trailing stop loss
            if percentage_difference < profit_activating_tsl:
                # print(f"""
                #       current_profit: {current_profit}
                #       profit_activating_tsl: {profit_activating_tsl}
                      
                #         loose_trailing_stop_loss: {loose_trailing_stop_loss}
                      
                #       stoploss_from_open(-hard_stop_loss, current_profit, is_short=trade.is_short, leverage=trade.leverage): {-loose_trailing_stop_loss}
                #       """)
                # at start or Negative profit, set hard stoploss as default
                return -loose_trailing_stop_loss
        
            else: # HIT! turn on TSL
                self.set_dfile_arg(pair, 'take_profit_hit', True)
                return -tight_trailing_stop_loss
            
        except ValueError as e:
            print(f"Error: get_dfile_arg in custom_stoploss: {e}")
            return None

        

    def input_strategy_data(self, pair: str):
        loose_trailing_stop_loss = float(
            input("Enter loose_trailing_stop_loss (NOTE: 1 == -1% TSL): ")) / 100
        profit_activating_tsl = float(
            input("Enter profit_activating_tsl (NOTE: 1 == +1% activate TSL): ")) / 100
        tight_trailing_stop_loss = float(
            input("Enter tight trailing_stop_loss (NOTE: 1 == -1% TSL): ")) / 100

        stake_amount = float(input("Enter stake amount (default is $10):  ")) 
        
        # print(f"""
              
        #         DEBUGGING input_strategy_data
        #         loose_trailing_stop_loss: {loose_trailing_stop_loss}
        #         profit_activating_tsl: {profit_activating_tsl}
        #         tight_trailing_stop_loss: {tight_trailing_stop_loss}
        #         stake_amount: {stake_amount}
        #         """)

        self.order_handler.update_strategy_data(pair, {
            "profit_activating_tsl": profit_activating_tsl,
            "tight_trailing_stop_loss": tight_trailing_stop_loss,
            "loose_trailing_stop_loss": loose_trailing_stop_loss,
            "take_profit_hit": False, # default "off"
            "stake_amount": stake_amount
        }, OrderStatus.PENDING)

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        
        try:
            loose_trailing_stop_loss = self.get_dfile_arg(
                pair, 'loose_trailing_stop_loss')
            tight_trailing_stop_loss = self.get_dfile_arg(
                pair, 'tight_trailing_stop_loss')
            profit_activating_tsl = self.get_dfile_arg(
                pair, 'profit_activating_tsl')
            dataframe.loc[dataframe.index[-1], ['enter_long',
                                                'enter_tag']] = (1, f"TP&TSL&SL_user_enter_(TP={profit_activating_tsl}, Loose_TSL={loose_trailing_stop_loss}, Tight_TSL={tight_trailing_stop_loss})")

        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None

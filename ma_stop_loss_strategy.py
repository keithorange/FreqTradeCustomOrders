
from datetime import datetime
import json
import time
from typing import Any, Dict, Optional
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import numpy as np
import pandas_ta as pta


from freqtrade.strategy.strategy_helper import stoploss_from_open
from custom_order_form_handler import OrderStatus
from file_loading_strategy import FileLoadingStrategy


def calculate_slope(y, window):
    """
    Calculate the slope of a linear regression line for each point in a series.
    The slope is calculated over a rolling window of size 'window' for the series 'y'.
    This function uses vectorization for fast computation.

    Args:
    y (np.array): The y-values of the data series.
    window (int): The number of points to consider for each linear regression calculation.

    Returns:
    np.array: An array of slope values.
    """
    # Ensure y is a numpy array for vectorized operations
    y = np.asarray(y)

    # The x values are the indices of y
    x = np.arange(len(y))

    # Expand x and y to have 'window' columns for vectorized operation
    x_mat = np.lib.stride_tricks.sliding_window_view(x, window_shape=window)
    y_mat = np.lib.stride_tricks.sliding_window_view(y, window_shape=window)

    # Calculate means of x and y within the window
    x_mean = np.mean(x_mat, axis=1)
    y_mean = np.mean(y_mat, axis=1)

    # Calculate the numerator and denominator of the slope formula
    numerator = np.sum(
        (x_mat - x_mean[:, None]) * (y_mat - y_mean[:, None]), axis=1)
    denominator = np.sum((x_mat - x_mean[:, None]) ** 2, axis=1)

    # Prevent division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        slope = np.true_divide(numerator, denominator)
        # If denominator is zero, slope is zero (horizontal line)
        slope[denominator == 0] = 0

    # Pad the result with NaN for the length of the window
    slope_padded = np.empty(len(y))
    slope_padded[:] = np.NaN
    slope_padded[window - 1:] = slope

    return slope_padded

class MAStopLossStrategy(FileLoadingStrategy):
    """
    Strategy that lets users choose between EMA and HMA for dynamic stop loss adjustment based on MA slope.
    """

    # Strategy configurations
    use_custom_stoploss = True
    stoploss = -1.0  # Default OFF


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        try:
            pair = metadata['pair']
            
            ma_type = self.get_dfile_arg(pair, 'ma_type')
            ma_period = self.get_dfile_arg(pair, 'ma_period')

                
            # EMA Calculation
            if ma_type == 'EMA':
                dataframe['ma'] = pta.ema(dataframe['close'], length=ma_period)
            # HMA Calculation
            elif ma_type == 'HMA':
                dataframe['ma'] = pta.hma(dataframe['close'], length=ma_period)

        except Exception as e:
            #print(f"(MASlopeStrategy) No order data found: {e}")
            return dataframe
        
        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        """
        Custom exit strategy that sets an exit signal based on a trailing stop loss which updates
        dynamically based on the moving average (MA) of the close price. It switches from a loose
        to a tight trailing stop loss once a certain profit target is hit.
        """
        
        # Retrieve the dataframe with the 'ma' column already calculated
        dataframe, _ = self.dp.get_analyzed_dataframe(
            pair=pair, timeframe=self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()

        # Retrieve strategy parameters from trade's custom_info or strategy configuration
        tight_trailing_stop_loss = self.get_dfile_arg(
            pair, 'tight_trailing_stop_loss')
        hard_stop_loss = self.get_dfile_arg(
        pair, 'hard_stop_loss')
        profit_activating_tsl = self.get_dfile_arg(pair, 'profit_activating_tsl')
        
        # if no trades return
        if not tight_trailing_stop_loss or not hard_stop_loss or not profit_activating_tsl:
            return None

        # Determine the highest MA encountered
        
        
        highest_ma = self.get_dfile_arg(pair, 'highest_ma')
        if not highest_ma:
            #print(f"(Highest MA not found): setting to last candle's MA {last_candle['ma']}")
            highest_ma = last_candle['ma']

        # If current MA is higher than the recorded highest MA, update the highest MA
        if last_candle['ma'] > highest_ma:
            highest_ma = last_candle['ma']
            self.set_dfile_arg(pair, 'highest_ma', highest_ma)

        # Check if the take profit has been hit to switch to tight trailing stop loss
        if not self.get_dfile_arg(pair, 'take_profit_hit') and current_profit > profit_activating_tsl / 100:
            self.set_dfile_arg(pair, 'take_profit_hit', True)

        # Calculate the trailing stop loss based on the highest MA
        if self.get_dfile_arg(pair, 'take_profit_hit'):
            tsl = highest_ma * (1 - tight_trailing_stop_loss / 100)
            if current_rate < tsl:
                return 'tight_trailing_stop_loss'
        else:
            
            # calcualte pct diff between LAST_CANDLE['ma'] and open rate, if it is less than -hard_stop_loss, return 'hard_stop_loss'
            # percentage_difference = ((current_rate - trade.open_rate) / trade.open_rate) * 100 related but not right
            percentage_difference = ((last_candle['ma'] - trade.open_rate) / trade.open_rate) * 100
            is_below_hard_stop_loss = percentage_difference < -hard_stop_loss
            
            # HARD STOP LOSS
            #tsl = highest_ma * (1 - loose_trailing_stop_loss / 100)
            print(f"pair {pair}\npercentage_difference: {percentage_difference}\n hard_stop_loss: {hard_stop_loss}\n is_below_hard_stop_loss: {is_below_hard_stop_loss}")
            if is_below_hard_stop_loss:
                print(f"(-hard_stop_loss HIT!) percentage_difference: {percentage_difference} hard_stop_loss: {hard_stop_loss}")
                return 'hard_stop_loss'

        return None


    def input_strategy_data(self, pair: str):
        
        ma_type = input("Choose between 'EMA' or 'HMA' for moving average type: ")
        ma_period = int(input("Enter the period for the moving average: "))
        
        
        hard_stop_loss = float(
            input("Initial (HARD) stop loss % (1 for -1%); this applies until your PROFIT-TARGET is hit: "))
        tight_trailing_stop_loss = float(
            input("Secondary (TIGHT) trailing stop loss % (1 for -1%): "))
        profit_activating_tsl = float(
            input("PROFIT-TARGET profit % to switch LOOSE TSL -> TIGHT TSL (1 for activation at 1% profit): "))
        
        stake_amount = float(input("Enter the amount you wish to invest in this trade (leave blank for $10 default):  "))

        order_data =  {
            "ma_type": ma_type,
            "ma_period": ma_period,
            
            "profit_activating_tsl": profit_activating_tsl,
            "take_profit_hit": False,  # default "off"
            "tight_trailing_stop_loss": tight_trailing_stop_loss,
            "hard_stop_loss": hard_stop_loss,
            "stake_amount": stake_amount
            }
        
        print("\nPlease review your order details:")
        print(json.dumps(order_data, indent=4))
        confirmation = input(
            "Type 'Y' to confirm and submit your order, anything else to cancel: ").upper()

        if confirmation == 'Y':
            self.order_handler.update_strategy_data(pair, order_data, OrderStatus.PENDING)
            print("\nSubmitted order!")
            print(json.dumps(order_data, indent=4))
        else:
            print("\nCancelled placing order!")

        time.sleep(3)


        self.order_handler.update_strategy_data(pair,order_data, OrderStatus.PENDING)

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        try:
            # get all from self.get_dfile_arg(pair,...)
            ma_type = self.get_dfile_arg(pair, 'ma_type')
            ma_period = self.get_dfile_arg(pair, 'ma_period')
            hard_stop_loss = self.get_dfile_arg(
                pair, 'hard_stop_loss')
            tight_trailing_stop_loss = self.get_dfile_arg(pair, 'tight_trailing_stop_loss')
            profit_activating_tsl = self.get_dfile_arg(pair, 'profit_activating_tsl')
            stake_amount = self.get_dfile_arg(pair, 'stake_amount')
            
            dataframe.loc[dataframe.index[-1], ['enter_long', 'enter_tag']] = (
                1, 
                f"(MAStopLossStrategy) ma_type={ma_type}, ma_period={ma_period}, hard_stop_loss={hard_stop_loss}, tight_trailing_stop_loss={tight_trailing_stop_loss}, profit_activating_tsl={profit_activating_tsl}, stake_amount={stake_amount}"
            )
        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None
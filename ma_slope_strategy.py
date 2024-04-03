
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

# def calculate_slope(dataframe, period):
#     slope = (dataframe - dataframe.shift(period)) / period
#     return slope

import numpy as np


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

# Example usage with a DataFrame:
# Assume 'df' is a pandas DataFrame and 'close' is the column with closing prices.
# window_size = 14  # for example, a two-week period
# df['ma_slope'] = calculate_fast_slope(df['close'].values, window_size)


class MASlopeStrategy(FileLoadingStrategy):
    """
    Strategy that lets users choose between EMA and HMA for dynamic stop loss adjustment based on MA slope.
    """

    # Strategy configurations
    use_custom_stoploss = True
    stoploss = -1.0  # Default OFF


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        try:
            #print(f"Metadata: {metadata}")
            pair = metadata['pair']
            
            ma_type = self.get_dfile_arg(pair, 'ma_type')
            ma_period = self.get_dfile_arg(pair, 'ma_period')
            slope_threshold = self.get_dfile_arg(pair, 'slope_threshold')
            slope_period = self.get_dfile_arg(pair, 'slope_period')
                
            # EMA Calculation
            if ma_type == 'EMA':
                dataframe['ma'] = pta.ema(dataframe['close'], length=ma_period)
            # HMA Calculation
            elif ma_type == 'HMA':
                dataframe['ma'] = pta.hma(dataframe['close'], length=ma_period)
            
            # Slope Calculation
            dataframe['ma_slope'] = calculate_slope(dataframe['ma'], slope_period)
            
        except Exception as e:
            #print(f"(MASlopeStrategy) No order data found: {e}")
            return dataframe
        
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,current_rate: float, current_profit: float, after_fill: bool,**kwargs) -> Optional[float]:
        """

        """
        
        # USE A STATIC STOPLOSS FOR-WORST-CASE 

        stop_loss_pct = self.get_dfile_arg(pair, 'stop_loss_pct')

        # Calculate stoploss relative to open price (no trailing)
        return stoploss_from_open(
            -stop_loss_pct / 100, current_profit, is_short=trade.is_short, leverage=trade.leverage)

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        try:
            pair = metadata['pair']
            slope_threshold = self.get_dfile_arg(pair, 'slope_threshold')
            # Define sell conditions
            dataframe.loc[
                (
                    # Updated sell condition: MA slope is under slope_threshold
                    (dataframe['ma_slope'] < slope_threshold)
                ),
            ['exit_long', 'exit_tag']] = (1, f"ma_slope_exit_{slope_threshold}")
            
        except Exception as e:
            # print(f"(MASlopeStrategy) Error: populate_exit_trend: {e}")
            pass
            
        return dataframe

    def input_strategy_data(self, pair: str):
        
        ma_type = input("Choose between 'EMA' or 'HMA' for moving average type: ")
        ma_period = int(input("Enter the ma_period for the moving average: "))
        slope_threshold = float(input("Enter the slope_threshold for the moving average slope: "))
        slope_period = int(input("Enter the period for the slope calculation: "))
        
        
        stop_loss_pct = float(input("Specify your hard stop loss as a percentage (e.g., '1' for 1% stop loss): "))
        stake_amount = float(input("Enter the amount you wish to invest in this trade (leave blank for $10 default):  "))

        order_data =  {
            "ma_type": ma_type,
            "ma_period": ma_period,
            "slope_period": slope_period,
            "slope_threshold": slope_threshold,
            "stop_loss_pct": stop_loss_pct,
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
            slope_period = self.get_dfile_arg(pair, 'slope_period')
            slope_threshold = self.get_dfile_arg(pair, 'slope_threshold')
            stop_loss_pct = self.get_dfile_arg(pair, 'stop_loss_pct')
            stake_amount = self.get_dfile_arg(pair, 'stake_amount')

            dataframe.loc[dataframe.index[-1], ['enter_long', 'enter_tag']] = (
                1, 
                f"(MASlopeStrategy) ma_type={ma_type}, ma_period={ma_period}, slope_period={slope_period}, slope_threshold={slope_threshold}, stop_loss_pct={stop_loss_pct}, stake_amount={stake_amount}"
            )
        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None
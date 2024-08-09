
from datetime import datetime, timedelta
from datetime import datetime
import json
import logging
import time
from typing import Any, Dict, Optional

from dateutil.relativedelta import relativedelta
from dateutil import parser

from freqtrade.persistence.trade_model import Order, Trade
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import numpy as np
import pandas_ta as pta

from custom_order_form_handler import OrderStatus
from file_loading_strategy import FileLoadingStrategy

from dateutil import parser

from exit_strategy_manager import ExitStrategyManager



class MATrailingStopLossStrategy(FileLoadingStrategy):
    """
    Strategy that lets users choose between EMA and HMA for dynamic stop loss adjustment based on MA slope.
    """

    # Strategy configurations
    use_custom_stoploss = True
    stoploss = -1.0  # Default OFF

    use_exit_signal = True
    # Schedule force exit in 3 minutes
    

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        try:
            # Ensure metadata contains the required keys
            if 'pair' not in metadata:
                raise KeyError("Metadata does not contain 'pair'.")
            pair = metadata['pair']

            # CHECK IF PAIR HAS ACTIVE ORDER (WILL CHECK ALL PAIRS IN PAIRLIST)
            if self.does_pair_have_active_order(pair):
                # Ensure price column exists in dataframe
                if 'close' not in dataframe.columns:
                    raise KeyError(
                        "Dataframe does not contain 'close' column.")

                current_close = dataframe['close'].iloc[-1]
                self.set_dfile_arg(pair, 'current_price', current_close)

                # Fetching values from self.get_dfile_arg
                ma_type = self.get_dfile_arg(pair, 'ma_type')
                ma_period = self.get_dfile_arg(pair, 'ma_period')

                # Check if ma_type and ma_period are properly set
                if ma_type is None or ma_period is None:
                    return dataframe  # early exit

                # EMA Calculation
                if ma_type.upper() == 'EMA':
                    dataframe['ma'] = pta.ema(
                        dataframe['close'], length=ma_period)
                # HMA Calculation
                elif ma_type.upper() == 'HMA':
                    dataframe['ma'] = pta.hma(
                        dataframe['close'], length=ma_period)
                else:
                    raise ValueError(f"(MA_TYPE ERROR!) {ma_type.upper()} MUST BE EITHER 'HMA' OR 'EMA'")

                # Ensure there are at least 30 MA values; otherwise, use available MA values
                n = 100
                last_n_ma = dataframe['ma'].iloc[-n:].tolist()
                if len(last_n_ma) < n:
                    logging.warning(f"Not enough data points for last_n_ma for pair {pair}. Using {len(last_n_ma)} data points.")

                # Ensure last_n_ma is a list and contains floats
                last_n_ma = [float(price) for price in last_n_ma]

                # Write MA values to log file
                self.set_dfile_arg(pair, 'prices', last_n_ma)

            else:
                pass

        except Exception as e:
            print(
                f"(ERROR!) MATrailingStopLossStrategy populate_indicators \nError: {e}\n")

        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        """
        Custom exit strategy that sets an exit signal based on a trailing stop loss which updates
        dynamically based on the moving average (MA) of the close price. It switches from a loose
        to a tight trailing stop loss once a certain profit target is hit. If tight_trailing_stop_loss is 0,
        auto-sell is triggered when take profit is hit.
        """
        # Retrieve the dataframe with the 'ma' column already calculated
        dataframe, _ = self.dp.get_analyzed_dataframe(
            pair=pair, timeframe=self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        price = last_candle['close']

        # Continue ONLY if have order data!
        if not self.does_pair_have_active_order(pair):
            return

        pct_diff = (
            (last_candle['ma'] - trade.open_rate) / trade.open_rate) * 100

        # Retrieve strategy parameters from trade's custom_info or strategy configuration
        tight_trailing_stop_loss = self.get_dfile_arg(
            pair, 'tight_trailing_stop_loss')
        loose_stop_loss = self.get_dfile_arg(pair, 'loose_stop_loss')
        is_loose_stop_loss_trailing = self.get_dfile_arg(
            pair, 'is_loose_stop_loss_trailing')
        take_profit = self.get_dfile_arg(pair, 'take_profit')
        take_profit_hit = self.get_dfile_arg(pair, 'take_profit_hit')
        highest_ma = self.get_dfile_arg(pair, 'highest_ma')

        if not highest_ma:
            highest_ma = last_candle['ma']

        # If current MA is higher than the recorded highest MA, update the highest MA
        if last_candle['ma'] >= highest_ma:
            highest_ma = last_candle['ma']
            self.set_dfile_arg(pair, 'highest_ma', highest_ma)

        # Check if the take profit has been hit to switch to tight trailing stop loss
        above_tp = (pct_diff) > take_profit
        if not take_profit_hit and above_tp:
            self.set_dfile_arg(pair, 'take_profit_hit', True)

        


        # Calculate the trailing stop loss based on the highest MA
        exit_reason = None
        if above_tp:
            if tight_trailing_stop_loss == 0:
                exit_reason = 'auto_sell_at_take_profit'
            else:
                tsl = highest_ma * (1 - tight_trailing_stop_loss / 100)
                if current_rate < tsl:
                    exit_reason = 'tight_trailing_stop_loss'
        else:
            if is_loose_stop_loss_trailing:
                tsl = highest_ma * (1 - loose_stop_loss / 100)
                if current_rate < tsl:
                    exit_reason = 'loose_stop_loss_trailing'
            else:
                is_below_loose_stop_loss = pct_diff < -loose_stop_loss
                if is_below_loose_stop_loss:
                    exit_reason = 'loose_stop_loss_static'

        if exit_reason:
            def write_exit_data_to_file():
                self.set_dfile_arg(pair, 'exit_price', price)
                # set profit %
                entry_price = self.get_dfile_arg(pair, 'entry_price')
                percentage_profit = ((price - entry_price) / entry_price) * 100
                self.set_dfile_arg(pair, 'profit', percentage_profit)
                
                # set status to EXITED            
                self.set_dfile_arg(pair,'status', OrderStatus.EXITED.value)

            write_exit_data_to_file()
            
            try:
                # force exit (remove limit make market in n mins)
                exit_manager = ExitStrategyManager(
                    url='http://localhost:6970/api/v1',
                    username='1',
                    password='1'
                )
                print(f"POOOO REMOVE THE TIME TESTING")
                exit_manager.schedule_force_exit(trade.id, wait_time=60*2) 
            except Exception as e:
                print(f"Failed to launch Limit->Market exiter proesss! :() Error: {e}")
                
            return exit_reason

    def input_strategy_data(self, pair: str):
        ma_type = input(
            "Choose between '(E)MA' or '(H)MA' for moving average type: ")
        if 'H' in ma_type.upper():
            ma_type = 'HMA'
        elif 'E' in ma_type.upper():
            ma_type = 'EMA'
        else:
            ma_type = 'input_error'

        ma_period = int(input("Enter the period for the moving average: "))
        loose_stop_loss = float(input(
            "Initial (LOOSE) stop loss % (1 for -1%); this applies until your PROFIT-TARGET is hit: "))
        is_loose_stop_loss_trailing = input(
            "Is LOOSE stop loss (T)railing or (S)tatic? (T or S): ").upper() == 'T'
        tight_trailing_stop_loss_str = input(
            "Secondary (TIGHT) trailing stop loss % (1 for -1%) (leave EMPTY or 0 for auto-sell at take profit): ")

        if not tight_trailing_stop_loss_str:
            tight_trailing_stop_loss = 100
            take_profit = 100  # deactivated
        else:
            tight_trailing_stop_loss = float(tight_trailing_stop_loss_str)
            take_profit = float(input(
                "PROFIT-TARGET profit % to switch LOOSE TSL -> TIGHT TSL (1 for activation at 1% profit): "))

        # Assertions to ensure valid input values
        assert take_profit > 0, "Take profit must be greater than 0."
        assert 0 <= loose_stop_loss < 10, "Loose stop loss must be between 0 and 10%."
        assert (0 <= tight_trailing_stop_loss < 10) or (tight_trailing_stop_loss ==
                                                        100), "Tight trailing stop loss must be between 0 and 10% (or deactivated == 100%)."

        stake_amount = float(input(
            "Enter the amount you wish to invest in this trade (leave blank for $10 default): "))

        use_entry_condition = input(
            "Use entry condition? (leave EMPTY for NONE): ")
        if use_entry_condition:
            print("Select entry condition type:")
            print("1: Price Crosses Upward Condition")
            print("2: Price Under Condition")
            print("3: Price Reverses Up Condition")

            # Get the user's choice
            condition_choice_int = input(
                "Enter the number of the entry condition: ").strip()

            # Map each int 1,2,3... to condition string name
            condition_mapping = {
                "1": "PriceCrossesUpwardCondition",
                "2": "PriceUnderCondition",
                "3": "PriceReversesUpCondition"
            }

            # Get the corresponding condition string name
            condition_choice = condition_mapping.get(condition_choice_int)

            # Specific parameters for different entry conditions
            if condition_choice in ['PriceCrossesUpwardCondition', 'PriceUnderCondition']:
                entry_condition_price = float(
                    input("Enter the target price for activation: "))
            else:
                entry_condition_price = None

            if condition_choice == 'PriceReversesUpCondition':
                threshold_pct_str = input(
                    "Enter % price reverses before activation (default=0.15): ")
                threshold_pct = float(
                    threshold_pct_str) if threshold_pct_str else 0.15

            timeout_minutes = int(input(
                "Enter the number of minutes for the entry condition timeout (e.g., 150 for 2.5 hours): "))
            timeout = datetime.now() + timedelta(minutes=timeout_minutes)

            order_status = OrderStatus.WAITING

        else:
            order_status = OrderStatus.PENDING
            entry_condition_price = None
            timeout = None

        order_data = {
            "status": order_status.value,
            "created_at": datetime.now().isoformat(),
            "stake_amount": stake_amount,
            "ma_type": ma_type,
            "ma_period": ma_period,
            "loose_stop_loss": loose_stop_loss,
            "is_loose_stop_loss_trailing": is_loose_stop_loss_trailing,
            "tight_trailing_stop_loss": tight_trailing_stop_loss,
            "take_profit": take_profit,
            "take_profit_hit": False,
            "highest_ma": 0,
            "entry_condition": condition_choice if use_entry_condition else None,
            "entry_condition_timeout": timeout.isoformat() if timeout else None,
            "entry_condition_price": entry_condition_price if use_entry_condition else None,
            # FOR REVERSE DIRECTION ENTRY CONDITION
            "threshold_pct": threshold_pct if (use_entry_condition and (condition_choice == 'PriceReversesUpCondition')) else None,
            "current_price": 0,
            "prices": [],
            # for keeping track of profit
            "entry_price": 0,
            "exit_price": 0,
            "profit": 0,
        }

        print("\nPlease review your order details:")
        print(json.dumps(order_data, indent=4))
        confirmation = input(
            "Type 'Y' to confirm and submit your order, anything else to cancel: ").upper()

        if confirmation == 'Y':
            self.order_handler.update_strategy_data(pair, order_data)
            print("\nSubmitted order!")
            print(json.dumps(order_data, indent=4))
        else:
            print("\nCancelled placing order!")

        time.sleep(3)

    # Update set_entry_signal method to include all variables in the string

    def set_entry_signal(self, pair: str, dataframe: DataFrame, data: Dict[str, Any]):
        try:
            ma_type = self.get_dfile_arg(pair, 'ma_type')
            ma_period = self.get_dfile_arg(pair, 'ma_period')
            loose_stop_loss = self.get_dfile_arg(pair, 'loose_stop_loss')
            is_loose_stop_loss_trailing = self.get_dfile_arg(
                pair, 'is_loose_stop_loss_trailing')
            tight_trailing_stop_loss = self.get_dfile_arg(
                pair, 'tight_trailing_stop_loss')
            take_profit = self.get_dfile_arg(pair, 'take_profit')
            stake_amount = self.get_dfile_arg(pair, 'stake_amount')
            entry_condition = self.get_dfile_arg(pair, 'entry_condition')

            dataframe.loc[dataframe.index[-1], ['enter_long', 'enter_tag']] = (
                1,
                f"(MATrailingStopLossStrategy) ma_type={ma_type} ma_period={ma_period} is_loose_stop_loss_trailing={is_loose_stop_loss_trailing} loose_stop_loss={loose_stop_loss} tight_trailing_stop_loss={tight_trailing_stop_loss} take_profit={take_profit} stake_amount={stake_amount} entry_condition={entry_condition}"
            )
        except Exception as e:
            print(f"Error: set_entry_signal: {e}")
            return None

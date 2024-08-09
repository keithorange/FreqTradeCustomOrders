from typing import List, Callable
import pandas as pd
import pandas_ta as pta


def calculate_ma(prices: List[float], period: int, ma_type: str) -> List[float]:
    df = pd.DataFrame(prices, columns=['price'])
    if ma_type.upper() == 'EMA':
        df['ma'] = pta.ema(df['price'], length=period)
    elif ma_type.upper() == 'HMA':
        df['ma'] = pta.hma(df['price'], length=period)
    else:
        raise ValueError(f"Unsupported moving average type: {ma_type}")
    return df['ma'].tolist()


def price_crosses_upward(target_price: float, last_prices: List[float]) -> bool:
    return last_prices[-2] < target_price <= last_prices[-1]


def price_under(target_price: float, last_prices: List[float]) -> bool:
    return last_prices[-1] < target_price


def price_reverses_up(last_prices: List[float], period: int, threshold_pct: float) -> bool:
    if len(last_prices) < 3:
        return False

    # Find the lowest price in the recent period
    lowest_price = min(last_prices[-period:])

    # Get the current price and the price before it
    current_price = last_prices[-1]
    previous_price = last_prices[-2]

    # Calculate the reversal threshold
    reversal_threshold = lowest_price * (1 + threshold_pct / 100)

    # Check if the price has reversed up by the threshold percentage
    price_reversed = current_price > reversal_threshold

    # Ensure the current price is higher than the previous price
    upward_movement = current_price > previous_price

    return price_reversed and upward_movement

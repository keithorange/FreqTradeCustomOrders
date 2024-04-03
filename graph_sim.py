import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt


def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()


def calculate_hma(prices, period):
    half_length = int(period / 2)
    sqrt_length = int(np.sqrt(period))
    wmaf = prices.rolling(window=half_length).mean()
    wmas = prices.rolling(window=period).mean()
    diff = 2 * wmaf - wmas
    return diff.rolling(window=sqrt_length).mean()


def calculate_slope(ma, n):
    return (ma.iloc[-1] - ma.iloc[-n]) / n


def apply_strategy(prices, ma_type='EMA', period=14, n=3, dip_depth=0):
    if ma_type.upper() == 'EMA':
        ma = calculate_ema(prices, period)
    elif ma_type.upper() == 'HMA':
        ma = calculate_hma(prices, period)
    else:
        raise ValueError("MA Type must be 'EMA' or 'HMA'")

    slopes = ma.rolling(window=n).apply(
        lambda x: calculate_slope(x, n), raw=False)
    sell_signals = slopes < dip_depth

    return ma, sell_signals


# if __name__ == '__main__':
#     # Simulate 100 random price points
#     np.random.seed(420)  # For reproducibility
#     prices = pd.Series(np.random.normal(0, 1, 1000).cumsum())
#     # Define period, n, and dip_depth
#     period = 16
#     n = 4
#     dip_depth = -0.0001

#     # Apply EMA strategy
#     ema, ema_sell_signals = apply_strategy(
#         prices, ma_type='EMA', period=period, n=n, dip_depth=dip_depth)

#     # Apply HMA strategy
#     hma, hma_sell_signals = apply_strategy(
#         prices, ma_type='HMA', period=period, n=n, dip_depth=dip_depth)

#     # Plotting
#     fig, axs = plt.subplots(2, 1, figsize=(14, 14))

#     # EMA Plot
#     axs[0].plot(prices.index, prices, label='Price', color='blue')
#     axs[0].plot(prices.index, ema, label='EMA', color='orange')
#     axs[0].scatter(ema_sell_signals[ema_sell_signals].index,
#                 prices[ema_sell_signals], color='red', label='EMA Sell Signal', marker='v')
#     axs[0].set_title(
#         f'EMA Strategy (Period: {period}, Slope Window: {n}, Dip Depth: {dip_depth})')
#     axs[0].set_xlabel('Time Period')
#     axs[0].set_ylabel('Price')
#     axs[0].legend()

#     # HMA Plot
#     axs[1].plot(prices.index, prices, label='Price', color='blue')
#     axs[1].plot(prices.index, hma, label='HMA', color='orange')
#     axs[1].scatter(hma_sell_signals[hma_sell_signals].index, prices[hma_sell_signals],
#                 color='red', label='HMA Sell Signal', marker='^')
#     axs[1].set_title(
#         f'HMA Strategy (Period: {period}, Slope Window: {n}, Dip Depth: {dip_depth})')
#     axs[1].set_xlabel('Time Period')
#     axs[1].set_ylabel('Price')
#     axs[1].legend()

#     plt.tight_layout()
#     plt.show()

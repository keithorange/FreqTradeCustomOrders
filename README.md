# Custom Orders for Freqtrade


![Logo](logo.png)

This project provides an extension to [Freqtrade](https://www.freqtrade.io/), a free and open-source crypto trading bot written in Python. It enables the creation and execution of custom order strategies that go beyond the default stop loss, custom stop loss, and strategy exit functionalities offered by Freqtrade. This includes more advanced order types like trailing stop losses and take-profit conditions, which are particularly useful for day trading on exchanges with limited order types (e.g., Kraken only allows one limit sell order, no "one cancels the other" orders, etc.).

## Overview

The core of this extension is a set of Python classes that inherit from Freqtrade's `IStrategy` interface, allowing users to define custom trading strategies with specialized entry and exit signals, stop loss conditions, and stake amounts. The extension is designed to be flexible, supporting various trading strategies and customization for specific trading pairs and exchanges.

Included strategies:
- **Static Stop Loss**: Executes a sell order when the asset's price drops below a predefined percentage from the buy price.
- **Trailing Stop Loss**: Adjusts the stop loss level as the price of the asset increases, locking in profits.
- **Take-Profit Activating Trailing Stop Loss**: Activates a trailing stop loss once a predefined profit percentage is reached.
- **Custom Orders**: Allows for the creation of any type of custom orders, catering to the specific needs and rules of different exchanges.

## Installation

1. Ensure you have Freqtrade installed and set up. Refer to the [official Freqtrade documentation](https://www.freqtrade.io/en/stable/) for installation instructions.
2. Clone this repository into your Freqtrade project directory.
3. Install any additional required dependencies (if any) via pip:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **Select a strategy**: Start by choosing one of the provided custom order strategies or create your own by extending the `FileLoadingStrategy` class.
   
2. **Input strategy data**: Before launching Freqtrade with your chosen strategy, use the `input_order_data()` function to input necessary parameters like stop loss percentages, take-profit levels, and stake amounts for each trading pair.

   Example:
   ```python
   from tp_activating_tsl_with_sl_strategy import TPActivatingTSLwithSLStrategy

   strategy = TPActivatingTSLwithSLStrategy(config)
   strategy.input_strategy_data("BTC/USD")
   ```

3. **Launch Freqtrade**: Start Freqtrade with your selected strategy using the following command:
   ```
   freqtrade trade --strategy YourStrategyClassName
   ```

   Replace `YourStrategyClassName` with the name of the class you're using, such as `TPActivatingTSLwithSLStrategy`.

4. **Monitor and adjust**: Your custom orders will now be managed according to the parameters you've set. You can monitor the bot's performance and adjust your strategy parameters as needed.

## Customization

To customize or create new strategies, extend the `FileLoadingStrategy` class and implement the necessary methods such as `custom_stoploss`, `input_strategy_data`, and `set_entry_signal`. Refer to the provided strategy classes for examples.

## Contributing

Contributions to this project are welcome! Whether it's adding new features, improving existing strategies, or fixing bugs, feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is released under the same license as Freqtrade, making it free and open-source software. You can use, modify, and distribute it under the terms of the license.

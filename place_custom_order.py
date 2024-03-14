
from tp_activating_tsl_with_inital_tsl_strategy import TPActivatingTSLwithInitialTSLStrategy
from stop_loss_strategy import StopLossStrategy
from trailing_stop_loss_strategy import  TrailingStopLossStrategy
from tp_activating_tsl_with_sl_strategy import TPActivatingTSLwithSLStrategy


def input_order_data():
    print("Available Strategies:")
    
    print("1: Stop Loss")
    print("2: Trailing Stop Loss")
    print("3: Take-Profit Activating TrailingStop (with Hard StopLoss)")
    print("4: Take-Profit Activating TrailingStop (with Initial TrailingStop)")
    strategy_choice = input("Enter the strategy number: ")
    pair = input("Enter the trading pair (ex. BTC/USD) or symbol (ex. BTC): ")
    
    pair = pair.upper()
    pair += "/USD"
    # remove duplicate "/USD"
    pair = pair.replace("/USD/USD", "/USD")
    

    if strategy_choice == "1":
        strategy = StopLossStrategy(dict())
        strategy.input_strategy_data(pair)
        
    elif strategy_choice == "2":
        strategy = TrailingStopLossStrategy(dict())
        strategy.input_strategy_data(pair)
        
    elif strategy_choice == "3":
        strategy = TPActivatingTSLwithSLStrategy(dict())
        strategy.input_strategy_data(pair)
        
    elif strategy_choice == "4":
        strategy = TPActivatingTSLwithInitialTSLStrategy(dict())
        strategy.input_strategy_data(pair)
    else:
        print("Invalid strategy number.")


if __name__ == "__main__":
    input_order_data()

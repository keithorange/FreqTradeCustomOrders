from pandas import DataFrame
from typing import Dict, Any
from enum import Enum, auto
from datetime import datetime
import signal
import subprocess
import os
import platform
import json
import time

# Assuming custom_order_form_handler.py is in the same directory
from custom_order_form_handler import OrderStatus, StrategyDataHandler
from ma_stop_loss_strategy import MAStopLossStrategy
from ma_slope_strategy import MASlopeStrategy
from ma_trailing_stop_strategy import MATrailingStopLossStrategy
from stop_loss_strategy import StopLossStrategy
from tp_activating_tsl_with_inital_tsl_strategy import TPActivatingTSLwithInitialTSLStrategy
from tp_activating_tsl_with_sl_strategy import TPActivatingTSLwithSLStrategy
from trailing_stop_loss_strategy import TrailingStopLossStrategy


import argparse


def clear_screen():

    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


def select_strategy():
    clear_screen()
    print("Available Strategies:")
    print("1: Stop Loss")
    print("2: Trailing Stop Loss")
    print("3: Take-Profit Activating TrailingStop (with Hard StopLoss)")
    print("4: Take-Profit Activating TrailingStop (with Initial TrailingStop)")
    print("5: MASlopeStrategy")
    print("6: MATrailingStopLossStrategy")
    print("7: MAStopLossStrategy")
    
    strategy_choice = input("Select a strategy number: ")

    strategies = {
        "1": "StopLossStrategy",
        "2": "TrailingStopLossStrategy",
        "3": "TPActivatingTSLwithSLStrategy",
        "4": "TPActivatingTSLwithInitialTSLStrategy",
        "5": "MASlopeStrategy",
        "6": "MATrailingStopLossStrategy",
        "7": "MAStopLossStrategy",
        
    }

    strategy_name = strategies.get(strategy_choice, "")
    if not strategy_name:
        print("Invalid choice, please try again.")
        return None

    return strategy_name


def select_pair(pairs_list):
    """Present the user with a list of pairs to select from or allow direct input."""
    clear_screen()
    print("Available Pairs:")
    for i, pair in enumerate(pairs_list, start=1):
        print(f"{i}: {pair}")
    print("\nNote: If the desired pair is not found, you can directly input it.")
    print("If the desired pair is not listed, ensure you add it into the pair list from the main menu.")
    pair_choice = input(
        "\nSelect a pair number or directly input a pair (ex. BTC/USD) and press Enter to cancel: ")

    if pair_choice.isdigit() and 1 <= int(pair_choice) <= len(pairs_list):
        return pairs_list[int(pair_choice) - 1]
    elif '/' in pair_choice:
        return pair_choice.upper()
    else:
        print("Invalid selection or cancellation requested.")
        return None



def load_pair_list():
    """Load the list of pairs from the pair_list.txt file."""
    with open(pair_list_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def view_or_edit_orders():
    clear_screen()
    print("1: View All Orders")
    print("2: Edit An Order")
    choice = input("Choose an option: ")

    if choice == "1":
        display_orders()
    elif choice == "2":
        edit_existing_orders()
    else:
        print("Invalid choice.")


def display_orders():
    clear_screen()
    global strategy_name
    if not strategy_name:
        return

    handler = StrategyDataHandler(strategy_name, base_dir)
    strategy_data = handler.read_strategy_data()
    
    if not strategy_data:
        print(f"No existing orders for {strategy_name}.")
    else:
        for pair, data in strategy_data.items():
            print(f"Pair: {pair}")
            for key, value in data['data'].items():
                print(f"  {key}: {value}")
            print(f"  Status: {data['status']}\n")
    input("\nPress Enter to return...")


def edit_existing_orders():
    """Function to edit existing orders."""
    global strategy_name
    if not strategy_name:
        return

    handler = StrategyDataHandler(strategy_name, base_dir)
    strategy_data = handler.read_strategy_data()

    if not strategy_data:
        print(f"No existing orders for {strategy_name}.")
        return

    pair_to_edit = select_pair(list(strategy_data.keys()))
    if pair_to_edit is None:
        return

    data_to_edit = strategy_data[pair_to_edit]
    print(f"\nEditing Order for Pair: {pair_to_edit}")
    print(json.dumps(data_to_edit, indent=4))


    # Editing 'data' part
    for key in data_to_edit['data'].keys():
        new_value = input(f"{key} (current: {data_to_edit['data'][key]}): ")
        if new_value:
            if key == "take_profit_hit":
                # This will correctly parse 'true', 'True', '1', 't', 'y', 'yes' as True, and everything else as False.
                data_to_edit['data'][key] = new_value.strip().lower() in [
                    'true', '1', 't', 'y', 'yes']
            else:
                data_to_edit['data'][key] = float(new_value) if new_value.replace('.', '', 1).isdigit() else new_value
                
    # Editing 'status' part
    print(f"Current status: {data_to_edit['status']}")
    new_status = input(
        "New status (PENDING/HOLDING/EXITED or leave blank to keep current): ").upper()
    if new_status in OrderStatus._value2member_map_:
        data_to_edit['status'] = new_status

    handler.update_strategy_data(
        pair_to_edit, data_to_edit['data'], OrderStatus[data_to_edit['status']])
    print(f"✅ Order for {pair_to_edit} updated successfully!")


def edit_pair_list():
    clear_screen()
    pairs = load_pair_list()

    print("Current Pair List:")
    for i, pair in enumerate(pairs, start=1):
        print(f"{i}: {pair}")

    action = input(
        "\nDo you want to add (a) or remove (r) pairs? (a/r): ").lower()
    base_symbol = "/USD"  # Default base symbol

    if action == 'a':
        input_pairs = input(
            "Enter pairs (ex. A/USD B C), '/USD' optional after first: ")
        input_pairs_list = [pair.upper(
        ) if '/' in pair else pair.upper() + base_symbol for pair in input_pairs.split()]
        for new_pair in input_pairs_list:
            if new_pair not in pairs:
                pairs.append(new_pair)
                print(f"{new_pair} added to the pair list.")
            else:
                print(f"{new_pair} is already in the pair list.")

    elif action == 'r':
        input_pairs = input("Enter indices or pairs to remove (ex. 1 2 or A/USD B/CAD): ").split()
        if all(item.isdigit() for item in input_pairs):  # If all inputs are indices
            indices_to_remove = sorted([int(idx) - 1 for idx in input_pairs], reverse=True)
            for idx in indices_to_remove:
                if 0 <= idx < len(pairs):
                    removed_pair = pairs.pop(idx)
                    print(f"Removed {removed_pair} from the pair list.")
        else:  # If inputs are symbols
            symbols_to_remove = [item.upper() for item in input_pairs]
            for symbol in symbols_to_remove:
                if symbol in pairs:
                    pairs.remove(symbol)
                    print(f"Removed {symbol} from the pair list.")
                else:
                    print(f"{symbol} not found in the pair list.")

    update_pair_list(pairs)  # updated to use the helper function
    restart_freqtrade()



strategy_name = None  # Global variable to store the strategy name


def restart_freqtrade():
    """Restart freqtrade by killing and then launching it, if enabled."""
    if args.launch_freqtrade:
        kill_freqtrade()
        launch_freqtrade()
        print("Freqtrade restarted.")
    else:
        print("Freqtrade process management is disabled.")


def launch_freqtrade():
    """Launch Freqtrade only if enabled."""
    if args.launch_freqtrade:
        global strategy_name
        # Ensure the logs directory exists
        logs_dir = "CUSTOM_ORDERS_LOGS"
        os.makedirs(logs_dir, exist_ok=True)
        # Construct log file names based on strategy and current time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_files = {
            "stdout": os.path.join(logs_dir, f"{strategy_name}_stdout_{timestamp}.log"),
            "stderr": os.path.join(logs_dir, f"{strategy_name}_stderr_{timestamp}.log")
        }
        # Prepare the command and launch Freqtrade
        command = f"bash ./user_data/strategies/run_custom_order_freqtrade.sh {strategy_name}"
        subprocess.Popen(command, shell=True, stdout=open(
            log_files["stdout"], "w"), stderr=open(log_files["stderr"], "w"))
        print(f"Freqtrade launched for '{strategy_name}'. Check logs in {logs_dir} for more details.\n")
    else:
        print("Launching Freqtrade is disabled.")


def kill_freqtrade():
    """Kill Freqtrade processes if enabled."""
    if args.launch_freqtrade:
        try:
            # Send SIGTERM to allow graceful shutdown
            subprocess.run(f"pkill -f '{strategy_name}'", shell=True)
            # Wait a bit to allow the process to terminate gracefully
            time.sleep(3)
            # Forcefully terminate any remaining processes
            subprocess.run(f"pkill -9 -f '{strategy_name}'", shell=True)
        except Exception as e:
            print(
                f"An error occurred while terminating Freqtrade processes: {e}")
    else:
        print("Killing Freqtrade processes is disabled.")




def place_new_order():
    global strategy_name
    if not strategy_name:
        return

    pairs_list = load_pair_list()
    pair = select_pair(pairs_list)
    if not pair:
        print("Pair selection cancelled.")
        return
    
    # Check if the pair is in the pair list, if not, add it
    if pair not in pairs_list:
        print(f"{pair} is not in the pair list. Adding it now...")
        pairs_list.append(pair)
        update_pair_list(pairs_list)  # updated to use the helper functio
        restart_freqtrade()


    # Rest of the code for placing a new order...



    # Depending on the selected strategy, instantiate the strategy class
    strategy_class = {
        "StopLossStrategy": StopLossStrategy,
        "TrailingStopLossStrategy": TrailingStopLossStrategy,
        "TPActivatingTSLwithSLStrategy": TPActivatingTSLwithSLStrategy,
        "TPActivatingTSLwithInitialTSLStrategy": TPActivatingTSLwithInitialTSLStrategy,
        "MASlopeStrategy": MASlopeStrategy,
        "MATrailingStopLossStrategy": MATrailingStopLossStrategy,
        "MAStopLossStrategy": MAStopLossStrategy
    }[strategy_name]

    # Instantiate and set up the strategy
    clear_screen()
    strategy = strategy_class(dict())
    strategy.input_strategy_data(pair, EASY_MODE)
    
    global strategy_data_handler
    all_order_data = strategy_data_handler.read_strategy_data()
    order_data = all_order_data[pair]
    print(f"Placing order: {order_data}")

    time.sleep(3)
    clear_screen()


def filter_orders_by_status(strategy_data, statuses):
    """Filter orders by given statuses."""
    return [pair for pair, data in strategy_data.items() if OrderStatus(data['status']) in statuses]



def update_pair_list(pairs):
    """Update the pair list with given pairs and sync it with current orders."""
    
    current_pairs = load_pair_list()
    with open(pair_list_path, 'w') as file:
        for pair in pairs:
            file.write(f"{pair}\n")
    print("Pair list updated.")
    
    # if current_pairs != pairs:
    #     print("Restarting Freqtrade to sync pair list with orders.")
    #     restart_freqtrade()


def sync_pairlist_to_orders():
    global strategy_name
    if not strategy_name:
        return
    
    global strategy_data_handler


    strategy_data = strategy_data_handler.read_strategy_data()

    valid_pairs = filter_orders_by_status(
        strategy_data, [OrderStatus.PENDING, OrderStatus.HOLDING])

    update_pair_list(valid_pairs)
    restart_freqtrade()


def remove_old_data():
    clear_screen()
    pairs_list = load_pair_list()

    # Read the orders for the current strategy
    orders = strategy_data_handler.read_strategy_data()

    print(f"all_orders for {strategy_name}: {orders}")

    # Step 1: Remove exited orders
    if input("Remove exited orders? (y/n): ").lower() == 'y':
        orders = {
            pair: data for pair, data in orders.items()
            if OrderStatus(data['status']) != OrderStatus.EXITED
        }

    # Step 2: Ensure all orders are in pair list
    if input("Remove orders not in pair list? (y/n): ").lower() == 'y':
        orders = {
            pair: data for pair, data in orders.items()
            if pair in pairs_list
        }

    # Step 3: Keep pairs with PENDING or HOLDING orders
    if input("Keep only pairs with PENDING or HOLDING orders? (y/n): ").lower() == 'y':
        orders = {
            pair: data for pair, data in orders.items()
            if OrderStatus(data['status']) in [OrderStatus.PENDING, OrderStatus.HOLDING]
        }

    # Update the pair list to reflect the changes
    updated_pairs_list = list(orders.keys())
    update_pair_list(updated_pairs_list)
    restart_freqtrade()

    # Save the updated orders
    strategy_data_handler.save_strategy_data(orders)


def main_menu():
    clear_screen()
    
    print("===== Custom Orders Management System =====")
    print("1: Place New Order 💰")
    print("2: Edit (or View) Existing Orders 🔧")
    if not EASY_MODE:

        print("3: Edit (or View) Pair List 🔧")
        print("4: Launch Freqtrade 🤖")
        print("5: Kill All Freqtrade 🤖")
        print("6: Remove Old Data 🔨")
        print("7: Exit")

    return input("Enter your choice: ")


strategy = None

# Initialize the StrategyDataHandler with the base_dir
strategy_data_handler = None



# for sergey and easy users
EASY_MODE = True
    
def run():
    
    
    global strategy_name
    
    if EASY_MODE:
        strategy_name = "MATrailingStopLossStrategy"  # select_strategy()
    else:
        strategy_name = select_strategy()
        
    global strategy_data_handler 
    strategy_data_handler = StrategyDataHandler(strategy_name, base_dir)
    
    # Sync pairlist to orders at the start
    sync_pairlist_to_orders()  # will auto launch freqtrade with the selected strategy


    time.sleep(1)
    
    while True:
        choice = main_menu()
        if choice == "1":
            place_new_order()
        elif choice == "2":
            view_or_edit_orders()
        elif choice == "3":
            edit_pair_list()
        elif choice == "4":
            launch_freqtrade()
        elif choice == "5":  # Handling the new option
            kill_freqtrade()
        elif choice == "6":
            remove_old_data()
        elif choice == "7":
            print("\nThank you for using the Custom Orders Management System.")
            break

        else:
            print("Invalid choice, please try again.")

        # Moved the input here to avoid pressing Enter twice
        input("\n\nPress Enter to continue...")

    print("Exiting the Custom Orders Management System.")
    print("LEAVING FreqTrade RUNNING! To stop it, use the 'Kill All Freqtrade' option, or restart the script!")


import webbrowser
# Ensure viertualenv is activated
import subprocess

if __name__ == "__main__":
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(
        description="Custom Orders Management System")
    parser.add_argument('--launch_freqtrade', action='store_true',
                        help='Enable automatic management of Freqtrade processes')
    args = parser.parse_args()
    
    # Open frequi
    url = "http://localhost:6970"
    webbrowser.open(url)

    

    # Activate the virtual environment
    subprocess.run(["source", ".venv/bin/activate"])

    # Global variables for paths
    base_dir = os.path.abspath('user_data/strategies')
    pair_list_path = os.path.abspath(os.path.join(base_dir, 'pair_list.txt'))
    run()

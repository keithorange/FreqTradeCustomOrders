import subprocess
import os
import platform
import json
import time

# Assuming custom_order_form_handler.py is in the same directory
from custom_order_form_handler import OrderStatus, StrategyDataHandler
from stop_loss_strategy import StopLossStrategy
from tp_activating_tsl_with_inital_tsl_strategy import TPActivatingTSLwithInitialTSLStrategy
from tp_activating_tsl_with_sl_strategy import TPActivatingTSLwithSLStrategy
from trailing_stop_loss_strategy import TrailingStopLossStrategy

# Global variables for paths
base_dir = os.path.abspath('user_data/strategies')
pair_list_path = os.path.abspath(os.path.join(base_dir, 'pair_list.txt'))

# Initialize the StrategyDataHandler with the base_dir
handler = StrategyDataHandler("", base_dir)


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
    strategy_choice = input("Select a strategy number: ")

    strategies = {
        "1": "StopLossStrategy",
        "2": "TrailingStopLossStrategy",
        "3": "TPActivatingTSLwithSLStrategy",
        "4": "TPActivatingTSLwithInitialTSLStrategy"
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
    strategy_name = select_strategy()
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
    strategy_name = select_strategy()
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
                data_to_edit['data'][key] = float(new_value)


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

        with open(pair_list_path, 'w') as file:
            for pair in sorted(pairs):
                file.write(f"{pair}\n")

        print("\nPair list updated.")


    with open(pair_list_path, 'w') as file:
        for pair in sorted(pairs):
            file.write(f"{pair}\n")

    print("\nPair list updated.")





def kill_all_freqtrade():
    clear_screen()
    try:
        command = ['./user_data/strategies/kill_freqtrade.sh']
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            print(f"❌ Failed to launch Freqtrade. Error:\n{stderr.decode()}")

        else:
            print(f"❌ Failed to kill Freqtrade processes. Error:\n{stderr.decode()}")

    except Exception as e:
        print(
            f"An error occurred while attempting to kill Freqtrade processes: {e}")


def run_script_in_tmux(script_path, strategy_name):
    tmux_session_name = "freqtrade_session"
    # Create a new tmux session
    subprocess.run(["tmux", "new-session", "-d", "-s", tmux_session_name])
    # Send the command to run the script in the tmux session
    subprocess.run(["tmux", "send-keys", "-t", tmux_session_name,
                   f"bash {script_path} {strategy_name}", "C-m"])
    print(f"Script is running in a detached tmux session named '{tmux_session_name}'.")
    print(
        f"To attach to the tmux session, run: 'tmux attach-session -t {tmux_session_name}'")
    print("To detach and leave the script running, press 'Ctrl+B' and then 'D'.")
    print("To terminate the script and close the tmux session, attach to it and then type 'exit'.")


def launch_freqtrade():
    strategy_name = select_strategy()
    if not strategy_name:
        return

    try:
        run_script_in_tmux(
                "./user_data/strategies/run_custom_order_freqtrade.sh", strategy_name)
        
        print(f"""✅ Freqtrade launched successfully with strategy: {
              strategy_name} 🤖""")
        

    except Exception as e:
        print(f"❌ Failed to launch Freqtrade. Error:\n{e}")




def place_new_order():
    """Function to place a new order."""
    strategy_name = select_strategy()
    if not strategy_name:
        return

    pairs_list = load_pair_list()
    pair = select_pair(pairs_list)
    if not pair:
        print("Pair selection cancelled.")
        return
    if pair not in pairs_list:
        print(f"{pair} is not in the pair list. Adding it now...")
        pairs_list.append(pair)
        with open(pair_list_path, 'w') as file:
            for p in pairs_list:
                file.write(f"{p}\n")


    # Depending on the selected strategy, instantiate the strategy class
    strategy_class = {
        "StopLossStrategy": StopLossStrategy,
        "TrailingStopLossStrategy": TrailingStopLossStrategy,
        "TPActivatingTSLwithSLStrategy": TPActivatingTSLwithSLStrategy,
        "TPActivatingTSLwithInitialTSLStrategy": TPActivatingTSLwithInitialTSLStrategy
    }[strategy_name]

    # Instantiate and set up the strategy
    clear_screen()
    strategy = strategy_class(dict())
    strategy.input_strategy_data(pair)
    
    all_order_data = strategy.order_handler.read_strategy_data()
    order_data = all_order_data[pair]
    #print(f"order_data {order_data}")

    time.sleep(3)
    clear_screen()


def remove_old_data():
    clear_screen()
    # Load existing orders and pair list
    pairs_list = load_pair_list()
    # Assuming this method exists and reads all orders across strategies
    all_orders = handler.read_all_strategy_data()

    # Step 1: Remove exited orders
    if input("Remove exited orders? (y/n): ").lower() == 'y':
        for strategy, orders in all_orders.items():
            all_orders[strategy] = {
                pair: data for pair, data in orders.items() if data['status'] != 'EXITED'}

    # Step 2: Remove orders not in pair list
    if input("Remove orders not in pair list? (y/n): ").lower() == 'y':
        for strategy, orders in all_orders.items():
            all_orders[strategy] = {pair: data for pair,
                                    data in orders.items() if pair in pairs_list}

    # Step 3: Remove pairs without orders
    if input("Remove pairs without orders? (y/n): ").lower() == 'y':
        pairs_with_orders = set(
            pair for orders in all_orders.values() for pair in orders)
        pairs_list = [pair for pair in pairs_list if pair in pairs_with_orders]

    # Save updates
    # Assuming this method exists and writes all orders across strategies
    handler.write_all_strategy_data(all_orders)
    with open(pair_list_path, 'w') as file:
        for pair in pairs_list:
            file.write(f"{pair}\n")

    print("Data cleanup complete.")


def run():
        

    def main_menu():
        clear_screen()
        print("===== Custom Orders Management System =====")
        print("1: Place New Order 💰")
        print("2: Edit (or View) Existing Orders 🔧")
        print("3: Edit (or View) Pair List 🔧")
        print("4: Launch Freqtrade 🤖")
        print("5: Kill All Freqtrade 🤖")
        print("6: Remove Old Data 🔨")
        print("\n******* Always RESET FreqTrade AFTER adding NEW PAIRS *******\n")
        print("7: Exit")


        return input("Enter your choice: ")
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
            kill_all_freqtrade()
        elif choice == "6":
            remove_old_data()
        elif choice == "7":
            print("\nThank you for using the Custom Orders Management System.")
            break

        else:
            print("Invalid choice, please try again.")

        # Moved the input here to avoid pressing Enter twice
        input("\n\nPress Enter to continue...")



if __name__ == "__main__":
    run()

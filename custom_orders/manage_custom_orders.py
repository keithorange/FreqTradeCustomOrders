import subprocess
import os
import platform
import json

# Assuming custom_order_form_handler.py is in the same directory
from custom_order_form_handler import OrderStatus, StrategyDataHandler
from stop_loss_strategy import StopLossStrategy
from tp_activating_tsl_with_inital_tsl_strategy import TPActivatingTSLwithInitialTSLStrategy
from tp_activating_tsl_with_sl_strategy import TPActivatingTSLwithSLStrategy
from trailing_stop_loss_strategy import TrailingStopLossStrategy

# Global variables for paths
base_dir = os.path.abspath('user_data/strategies/custom_orders')
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



def edit_existing_orders():
    """Function to edit existing orders."""
    strategy_name = select_strategy()
    if not strategy_name:
        return

    handler = StrategyDataHandler(strategy_name, base_dir)
    strategy_data = handler.read_strategy_data()

    if not strategy_data:
        print("No existing orders to edit.")
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
            data_to_edit['data'][key] = float(
                new_value) if key != "take_profit_hit" else new_value.lower() == 'true'

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

    choice = input("\nDo you want to add (a) or remove (r) a pair? (a/r): ")
    if choice.lower() == 'a':
        new_pair = input("Enter the new pair (ex. BTC/USD): ").strip().upper()
        if new_pair not in pairs:
            pairs.append(new_pair)
            print(f"{new_pair} added to the pair list.")
        else:
            print(f"{new_pair} is already in the pair list.")
    elif choice.lower() == 'r':
        remove_choice = input(
            "Enter the pair to remove or its index (ex. BTC/USD or 1): ")
        if remove_choice.isdigit() and 1 <= int(remove_choice) <= len(pairs):
            removed_pair = pairs.pop(int(remove_choice) - 1)
            print(f"{removed_pair} removed from the pair list.")
        elif remove_choice.upper() in pairs:
            pairs.remove(remove_choice.upper())
            print(f"{remove_choice.upper()} removed from the pair list.")
        else:
            print("Pair not found or invalid index.")
    else:
        print("Invalid choice.")
        return

    with open(pair_list_path, 'w') as file:
        for pair in pairs:
            file.write(f"{pair}\n")

    print("\nPair list updated.")




def kill_all_freqtrade():
    clear_screen()
    try:
        command = ['./user_data/strategies/custom_orders/kill_freqtrade.sh']
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
                "./user_data/strategies/custom_orders/run_custom_order_freqtrade.sh", strategy_name)
        
        print(f"""✅ Freqtrade launched successfully with strategy: {
              strategy_name} 🤖""")
        

    except Exception as e:
        print(f"❌ Failed to launch Freqtrade. Error:\n{e}")



def main_menu():
    clear_screen()
    print("===== Custom Orders Management System =====")
    print("1: Place New Order 💰")
    print("2: Edit Existing Orders 🔧")
    print("3: Edit Pair List 🔧")
    print("4: Launch Freqtrade 🤖")
    print("5: Kill All Freqtrade 🤖")
    print("6: Exit")

    return input("Enter your choice: ")


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

    # Depending on the selected strategy, instantiate the strategy class
    strategy_class = {
        "StopLossStrategy": StopLossStrategy,
        "TrailingStopLossStrategy": TrailingStopLossStrategy,
        "TPActivatingTSLwithSLStrategy": TPActivatingTSLwithSLStrategy,
        "TPActivatingTSLwithInitialTSLStrategy": TPActivatingTSLwithInitialTSLStrategy
    }[strategy_name]

    strategy = strategy_class(dict())
    strategy.input_strategy_data(pair)

    # Check if the order was saved successfully
    try:
        new_data = strategy.order_handler.read_strategy_data()[pair]
        print(f"✅ Order for {pair} successfully saved! Data: {new_data}")
    except Exception as e:
        print(f"Error: {e}\nOrder not saved. Please try again.")


def run():
    while True:
        choice = main_menu()
        if choice == "1":
            place_new_order()
        elif choice == "2":
            edit_existing_orders()
        elif choice == "3":
            edit_pair_list()
        elif choice == "4":
            launch_freqtrade()
        elif choice == "5":  # Handling the new option
            kill_all_freqtrade()
        elif choice == "6":
            print("\nThank you for using the Custom Orders Management System.")
            break
        else:
            print("Invalid choice, please try again.")

        # Moved the input here to avoid pressing Enter twice
        input("\n\nPress Enter to continue...")



if __name__ == "__main__":
    run()

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


def load_pair_list():
    """Load the list of pairs from the pair_list.txt file."""
    with open(pair_list_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def select_pair(pairs_list):
    """Present the user with a list of pairs to select from."""
    clear_screen()
    print("Available Pairs:")
    for i, pair in enumerate(pairs_list, start=1):
        print(f"{i}: {pair}")
    print("\nNote: If the desired pair is not found, ensure you add it into the pair list from the main menu.")
    pair_choice = input("\nSelect a pair number or press Enter to cancel: ")
    if not pair_choice.isdigit() or int(pair_choice) < 1 or int(pair_choice) > len(pairs_list):
        print("Invalid selection or cancellation requested.")
        return None
    return pairs_list[int(pair_choice) - 1]


def edit_existing_orders():
    """Function to edit existing orders."""
    strategy_name = select_strategy()
    if not strategy_name:
        return

    handler = StrategyDataHandler(strategy_name, base_dir)
    strategy_data = handler.read_strategy_data()

    if not strategy_data:
        print("No existing orders to edit.")
        input("\nPress Enter to return to the main menu...")
        return

    pair_to_edit = select_pair(list(strategy_data.keys()))
    if pair_to_edit is None:
        input("\nPress Enter to return to the main menu...")
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
    input("\nPress Enter to return to the main menu...")


    input("\nPress Enter to return to the main menu...")


def edit_pair_list():
    clear_screen()
    pairs = set()
    if os.path.exists(pair_list_path):
        with open(pair_list_path, 'r') as file:
            pairs = set(line.strip().upper() for line in file if line.strip())

    print("Current Pair List:")
    for pair in sorted(pairs):
        print(pair)

    choice = input("\nDo you want to add (a) or remove (r) a pair? (a/r): ")
    if choice.lower() == 'a':
        edit_pair = input("Enter the new pair (ex. BTC/USD): ").strip().upper()
        pairs.add(edit_pair)
    elif choice.lower() == 'r':
        edit_pair = input(
            "Enter the pair to remove (ex. BTC/USD): ").strip().upper()
        pairs.discard(edit_pair)
    else:
        input("No valid choice made. Press Enter to return to the main menu...")
        return

    with open(pair_list_path, 'w') as file:
        file.write('\n'.join(sorted(pairs)))

    print(f"✅ Order for {edit_pair} updated successfully!")

    input("Press Enter to return to the main menu...")


def kill_all_freqtrade():
    clear_screen()
    try:
        command = ['./kill_freqtrade.sh']
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
    input("\nPress Enter to return to the main menu...")


def launch_freqtrade():
    strategy_name = select_strategy()
    if not strategy_name:
        return

    command = ['./run_custom_order_freqtrade.sh', strategy_name]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        print(f"""✅ Freqtrade launched successfully with strategy: {
              strategy_name} 🤖\nProcess ID: {process.pid}""")

    else:
        print(f"❌ Failed to launch Freqtrade. Error:\n{stderr.decode()}")

    input("\nPress Enter to return to the main menu...")


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
        input("\nPress Enter to return to the main menu...")
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

    input("\nPress Enter to return to the main menu...")

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
            input("Press Enter to continue...")

        # Moved the input here to avoid pressing Enter twice
        if choice not in ["2", "3", "4", "5"]:
            input("Press Enter to continue...")



if __name__ == "__main__":
    run()

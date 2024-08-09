import json
import os
import portalocker
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List


class OrderStatus(Enum):
    PENDING = 'PENDING'  # ORDER READY TO READ AND ORDER KRAKEN NOT YET FINALIZED
    HOLDING = 'HOLDING'
    EXITED = 'EXITED'
    WAITING = 'WAITING'  # ENTRY CONDITION WAITING 
    CANCELED = 'CANCELED'


# Lists for order statuses (using string values)
ACTIVE_ORDER_STATUSES_VALUES = [
    OrderStatus.WAITING.value, OrderStatus.PENDING.value, OrderStatus.HOLDING.value]
INACTIVE_ORDER_STATUSES_VALUES = [
    OrderStatus.EXITED.value, OrderStatus.CANCELED.value]
ALL_ORDER_STATUSES_VALUES = ACTIVE_ORDER_STATUSES_VALUES + \
    INACTIVE_ORDER_STATUSES_VALUES


class StrategyDataHandler:
    def __init__(self, strategy_name: str, base_dir='.'):
        self.strategy_name = strategy_name
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(script_dir, base_dir)
        self.ensure_base_dir()
        self.live_trades_file = f"LIVE_TRADES_LOG_{self.strategy_name}.json"
        self.completed_trades_file = f"COMPLETED_TRADES_LOG_{self.strategy_name}.json"

    def ensure_base_dir(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def get_order_file_path(self) -> str:
        return os.path.join(self.base_dir, self.live_trades_file)

    def get_completed_trades_file_path(self) -> str:
        return os.path.join(self.base_dir, self.completed_trades_file)

    def read_file_with_lock(self, file_path: str) -> Any:
        with portalocker.Lock(file_path, 'r', timeout=10) as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []

    def write_file_with_lock(self, file_path: str, data: Any):
        with portalocker.Lock(file_path, 'w', timeout=10) as file:
            json.dump(data, file, indent=4)

    def read_strategy_data(self) -> Dict[str, Any]:
        file_path = self.get_order_file_path()
        if os.path.exists(file_path):
            return self.read_file_with_lock(file_path)
        return {}

    def save_strategy_data(self, data: Dict[str, Any]) -> None:
        sorted_data = dict(sorted(data.items(), key=lambda item: item[0]))
        file_path = self.get_order_file_path()
        
        with portalocker.Lock(file_path, 'r+', timeout=10) as file:
            try:
                strategy_data = json.load(file)
            except json.JSONDecodeError:
                strategy_data = {}
            
            for pair, pair_data in sorted_data.items():
                strategy_data = self.move_data_from_active_to_completed(pair, pair_data, strategy_data)
            
            file.seek(0)
            file.truncate()
            json.dump(strategy_data, file, indent=4)

    def read_completed_trades(self) -> List[Dict[str, Any]]:
        file_path = self.get_completed_trades_file_path()
        if os.path.exists(file_path):
            return self.read_file_with_lock(file_path)
        return []

    def save_completed_trades(self, data: List[Dict[str, Any]]) -> None:
        file_path = self.get_completed_trades_file_path()
        self.write_file_with_lock(file_path, data)
        
    def move_data_from_active_to_completed(self, pair, data, strategy_data):
        if data['status'] in [OrderStatus.EXITED.value, OrderStatus.CANCELED.value]:
            exited_trade = strategy_data.pop(pair, None)
            if exited_trade:
                exited_trade['status'] = OrderStatus.EXITED.value
                self.add_completed_trade(pair, exited_trade)
        else:
            strategy_data[pair] = data
            
        return strategy_data

    def update_strategy_data(self, pair, data):
        file_path = self.get_order_file_path()
        with portalocker.Lock(file_path, 'r+', timeout=10) as file:
            try:
                strategy_data = json.load(file)

                strategy_data = self.move_data_from_active_to_completed(pair, data, strategy_data)
                
                file.seek(0)
                file.truncate()
                json.dump(strategy_data, file, indent=4)
            except json.JSONDecodeError:
                # Handle empty or corrupted file
                strategy_data = {pair: data}
                json.dump(strategy_data, file, indent=4)

    def add_completed_trade(self, pair, trade_data):
        file_path = self.get_completed_trades_file_path()
        with portalocker.Lock(file_path, 'r+', timeout=10) as file:
            try:
                completed_trades = json.load(file)
                if not isinstance(completed_trades, list):
                    completed_trades = []
                completed_trades.append({pair: trade_data})
                file.seek(0)
                file.truncate()
                json.dump(completed_trades, file, indent=4)
            except json.JSONDecodeError:
                # Handle empty or corrupted file
                completed_trades = [{pair: trade_data}]
                json.dump(completed_trades, file, indent=4)


# outdated uses dict for cmpleted rtades

# import json
# import os
# import portalocker
# from datetime import datetime
# from enum import Enum
# from typing import Dict, Any


# class OrderStatus(Enum):
#     PENDING = 'PENDING' # ORDER READY TO READ AND ORDER KRAKEN NOT YET FINALIZED
#     HOLDING = 'HOLDING'
#     EXITED = 'EXITED'
#     WAITING = 'WAITING' # ENTRY CONDITION WAITING 
#     CANCELED = 'CANCELED'


# # Lists for order statuses (using string values)
# ACTIVE_ORDER_STATUSES_VALUES = [
#     OrderStatus.WAITING.value, OrderStatus.PENDING.value, OrderStatus.HOLDING.value]
# INACTIVE_ORDER_STATUSES_VALUES = [
#     OrderStatus.EXITED.value, OrderStatus.CANCELED.value]
# ALL_ORDER_STATUSES_VALUES = ACTIVE_ORDER_STATUSES_VALUES + \
#     INACTIVE_ORDER_STATUSES_VALUES


# class StrategyDataHandler:
#     def __init__(self, strategy_name: str, base_dir='.'):
#         self.strategy_name = strategy_name
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         self.base_dir = os.path.join(script_dir, base_dir)
#         self.ensure_base_dir()
#         self.live_trades_file = f"LIVE_TRADES_LOG_{self.strategy_name}.json"
#         self.completed_trades_file = f"COMPLETED_TRADES_LOG_{self.strategy_name}.json"

#     def ensure_base_dir(self):
#         if not os.path.exists(self.base_dir):
#             os.makedirs(self.base_dir)

#     def get_order_file_path(self) -> str:
#         return os.path.join(self.base_dir, self.live_trades_file)

#     def get_completed_trades_file_path(self) -> str:
#         return os.path.join(self.base_dir, self.completed_trades_file)

#     def read_file_with_lock(self, file_path: str) -> Dict[str, Any]:
#         with portalocker.Lock(file_path, 'r', timeout=10) as file:
#             try:
#                 return json.load(file)
#             except json.JSONDecodeError:
#                 return {}

#     def write_file_with_lock(self, file_path: str, data: Dict[str, Any]):
#         with portalocker.Lock(file_path, 'w', timeout=10) as file:
#             json.dump(data, file, indent=4)

#     def read_strategy_data(self) -> Dict[str, Any]:
#         file_path = self.get_order_file_path()
#         if os.path.exists(file_path):
#             return self.read_file_with_lock(file_path)
#         return {}

#     def save_strategy_data(self, data: Dict[str, Any]) -> None:
#         sorted_data = dict(sorted(data.items(), key=lambda item: item[0]))
#         file_path = self.get_order_file_path()
#         self.write_file_with_lock(file_path, sorted_data)

#     def read_completed_trades(self) -> Dict[str, Any]:
#         file_path = self.get_completed_trades_file_path()
#         if os.path.exists(file_path):
#             return self.read_file_with_lock(file_path)
#         return {}

#     def save_completed_trades(self, data: Dict[str, Any]) -> None:
#         sorted_data = dict(sorted(data.items(), key=lambda item: item[0]))
#         file_path = self.get_completed_trades_file_path()
#         self.write_file_with_lock(file_path, sorted_data)

#     def update_strategy_data(self, pair, data):
#         file_path = self.get_order_file_path()
#         with portalocker.Lock(file_path, 'r+', timeout=10) as file:
#             try:
#                 strategy_data = json.load(file)

#                 if data['status'] in [OrderStatus.EXITED.value, OrderStatus.CANCELED.value]:
#                     exited_trade = strategy_data.pop(pair, None)
#                     if exited_trade:
#                         exited_trade['status'] = OrderStatus.EXITED.value
#                         self.add_completed_trade(pair, exited_trade)
#                 else:
#                     strategy_data[pair] = data

#                 file.seek(0)
#                 file.truncate()
#                 json.dump(strategy_data, file, indent=4)
#             except json.JSONDecodeError:
#                 # Handle empty or corrupted file
#                 strategy_data = {pair: data}
#                 json.dump(strategy_data, file, indent=4)

#     def add_completed_trade(self, pair, trade_data):
#         file_path = self.get_completed_trades_file_path()
#         with portalocker.Lock(file_path, 'r+', timeout=10) as file:
#             try:
#                 completed_trades = json.load(file)
#                 completed_trades[pair] = trade_data
#                 file.seek(0)
#                 file.truncate()
#                 json.dump(completed_trades, file, indent=4)
#             except json.JSONDecodeError:
#                 # Handle empty or corrupted file
#                 completed_trades = {pair: trade_data}
#                 json.dump(completed_trades, file, indent=4)

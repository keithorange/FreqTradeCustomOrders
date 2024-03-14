
from datetime import datetime
import json
from enum import Enum, auto
from typing import Dict, Any
import os

from pandas import DataFrame

from datetime import datetime
import json
from enum import Enum, auto
from typing import Dict, Any
import os

from pandas import DataFrame


class OrderStatus(Enum):
    PENDING = 'PENDING'
    HOLDING = 'HOLDING'
    EXITED = 'EXITED'


class StrategyDataHandler:
    def __init__(self, strategy_name: str, base_dir='custom_orders'):
        self.strategy_name = strategy_name
        # Use an absolute path for base_dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(script_dir, base_dir)
        self.ensure_base_dir()

    def ensure_base_dir(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def get_order_file_path(self) -> str:
        return os.path.join(self.base_dir, f"{self.strategy_name}_orders.json")

    def read_strategy_data(self) -> Dict[str, Any]:
        file_path = self.get_order_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        return {}

    def save_strategy_data(self, data: Dict[str, Any]) -> None:
        file_path = self.get_order_file_path()
        temp_file_path = file_path + ".tmp"
        with open(temp_file_path, 'w') as file:
            json.dump(data, file, indent=4)
        os.replace(temp_file_path, file_path)

    def update_strategy_data(self, pair: str, data: Dict[str, Any], status: OrderStatus) -> None:
        strategy_data = self.read_strategy_data()
        strategy_data[pair] = {"data": data, "status": status.value}
        
        print(f"""
              
              DEBUGGGING update_strategy_data
                pair: {pair}
                data: {data}
                strategy_data: {strategy_data}
              """)
        
        self.save_strategy_data(strategy_data)


    

   



# Example usage for LazyStopLossStrategy
# lazy_stop_loss_strategy = LazyStopLossUserOrderInput)
# lazy_stop_loss_strategy.input_strategy_data("BTC/USDT")
# Assume 'dataframe' and 'metadata' are provided from the strategy context
# dataframe = lazy_stop_loss_strategy.populate_entry_trend(dataframe, metadata)

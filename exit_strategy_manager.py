import threading
import time
from freqtrade_client import FtRestClient

class ExitStrategyManager:
    """
    Manages exit strategies using Freqtrade's REST API, allowing limit orders to switch to market orders
    after a specified wait time.
    """
    def __init__(self, url, username, password):
        self.client = FtRestClient(url, username, password)

    def force_exit(self, trade_id):
        """
        Force exit a trade by ID using a market order.
        """
        response = self.client.forceexit(trade_id, ordertype='market')
        return response

    def wait_and_force_exit(self, trade_id, wait_time):
        """
        Wait for a specified time and then force exit the trade using a market order.
        """
        time.sleep(wait_time)
        self.force_exit(trade_id)

    def schedule_force_exit(self, trade_id, wait_time):
        """
        Schedule a force exit after a specified wait time in a separate thread.
        """
        threading.Thread(target=self.wait_and_force_exit, args=(trade_id, wait_time)).start()

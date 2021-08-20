import pandas as pd

class InventoryReader:
    """Handles reading LTAR Data Inventory
    """

    def __init__(self):
        print("Init")

    def read_inventory(self, file_path: str):
        """Reads csv file at file_path and returns a pandas dataframe
        """
        
        print("read_inventory")
        
        df = pd.read_csv(file_path)

        return df
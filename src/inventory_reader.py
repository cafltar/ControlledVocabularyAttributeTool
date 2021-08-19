import pandas as pd

class InventoryReader:
    def __init__(self):
        print("Init")

    def read_inventory(self, file_path: str):
        print("read_inventory")
        
        df = pd.read_csv(file_path)

        return df
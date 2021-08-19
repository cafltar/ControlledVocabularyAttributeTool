import pandas as pd
import json

import controlled_variable_attributes
import inventory_attribute

class AttributeReader:
    def __init__(self):
        print("Init")

    def read_attribute_file(self, file_path:str):
        print("read_attribute_file")

        df = pd.read_csv(file_path)

        attribute_dict = {}
        attribute_cols = []

        for index, row in df.iterrows():
            var_name = row["ControlledVariable"]
            var_attribute = controlled_variable_attributes.ControlledVariableAttributes(var_name)

            attribute_cols = [col for col in list(df.columns) if col.startswith('Attribute')]

            for attribute_col in attribute_cols:
                attribute = None
                if not pd.isna(row[attribute_col]):
                    attrib_string = row[attribute_col]
                    attribute = self.parse_attribute_string(attrib_string)

                var_attribute.append(attribute)

            attribute_dict[var_name] = var_attribute

        return attribute_dict, attribute_cols
                    

    def parse_attribute_string(self, attribute_string:str):
        components = attribute_string.split('|')

        inputType = components[0]
        label = components[1]
        options = None

        if len(components) > 2:
            options = json.loads(components[2])

        attribute = inventory_attribute.InventoryAttribute(
            inputType,
            label,
            options
        )

        return attribute
import inventory_attribute

class ControlledVariableAttributes:

    def __init__(self, controlled_variable_name):
        self.controlled_variable_name = controlled_variable_name
        self.attributes = []

    def append(self, attribute:inventory_attribute.InventoryAttribute):
        self.attributes.append(attribute)
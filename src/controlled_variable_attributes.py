import inventory_attribute

class ControlledVariableAttributes:
    """Represents a collection of attributes that correspond to a controlled variable term
    """

    def __init__(self, controlled_variable_name):
        self.controlled_variable_name = controlled_variable_name
        self.attributes = []

    def append(self, attribute:inventory_attribute.InventoryAttribute):
        """ Appends an InventoryAttribute to self's list of attributes
        """
        
        self.attributes.append(attribute)
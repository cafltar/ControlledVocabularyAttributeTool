class InventoryAttribute:
    """Represent a controlled variable term attribute
    """
    
    def __init__(self, attrib_type, name, values):
        self.attrib_type = attrib_type
        self.label = name
        self.values = values
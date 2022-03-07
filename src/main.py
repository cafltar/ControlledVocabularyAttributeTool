from attribute_reader import AttributeReader
import google_sheets_io
import inventory_reader
import inventory_attribute
import attribute_reader

import pandas as pd
import pathlib

def main(
    path_to_inventory, 
    path_to_attributes,
    path_to_token, 
    path_to_credentials):
    print("Main")
    """Entry point of the program. Orchestrates the creation of Google Sheets based attribute tools and writes them to the root of user's Google Drive"""

    # Last column with site-specific information (like SiteVariableName)
    SPREADSHEET_SITE_COL_END = 4
    
    # Column were attributes are to be appended to
    SPREADSHEET_ATTRIBUTE_COL_START = 8
    
    CONTROLLED_VARIABLE_COL_NAME = 'ControlledVariable'

    # Read soil-specific data inventory (also does some cleaning) <-- code smell!
    reader = inventory_reader.InventoryReader()
    inventory = reader.read_inventory(path_to_inventory)

    # Fill na's with blanks
    inventory.fillna('', inplace=True)

    # Read attributes file and get a dictionary of attributes corresponding to each controlled variable
    attrib_reader = attribute_reader.AttributeReader()
    attributes_dict, attribute_cols = attrib_reader.read_attribute_file(path_to_attributes)

    # Write a Spreadsheet for each site
    writer = google_sheets_io.GoogleSheetsIO(
        path_to_token, 
        path_to_credentials)

    site_ids = inventory["LTARSiteCode"].unique()

    # !!! temp !!!
    site_ids = ['PRHPA']
    # !!!!!!!!!!!!

    spreadsheetIds = []
    for site_id in site_ids:
        site_inventory = inventory[inventory["LTARSiteCode"] == site_id].reset_index(drop=True)

        spreadsheetId = writer.create_sheet(
            f'Attributes_{site_id}',
            site_inventory)
        spreadsheetIds.append(spreadsheetId)

        print(f"Wrote to {spreadsheetId}")

        # Add attribute columns
        writer.add_columns(
            spreadsheetId, 
            SPREADSHEET_ATTRIBUTE_COL_START, 
            len(attribute_cols))

        # Add headers for attribute columns
        writer.add_column_names(
            spreadsheetId,
            0,
            SPREADSHEET_ATTRIBUTE_COL_START,
            attribute_cols
        )
        
        # Add inputs
        controlled_var_col = site_inventory[CONTROLLED_VARIABLE_COL_NAME]
        for index, value in controlled_var_col.items():
            if value:
                attrib = attributes_dict.get(value)
                #attrib = attributes_dict[value]
                if attrib:
                    writer.create_inputs(
                        spreadsheetId,
                        attrib, 
                        index+1,                            #+1 for header
                        SPREADSHEET_ATTRIBUTE_COL_START)   

        # Format the document
        writer.add_formatting(
            spreadsheetId,
            SPREADSHEET_SITE_COL_END,
            SPREADSHEET_ATTRIBUTE_COL_START, 
            len(attribute_cols))

if __name__ == '__main__':
    inventory_path = pathlib.Path.cwd() / 'data' / 'input' / 'LtarSoilDataInventory_20211020edits_Downloaded20220307.csv'
    attributes_path = pathlib.Path.cwd() / 'data' / 'input' / 'SoilControlledVocabCodedAttrib_20220207.csv'

    main(
        inventory_path,
        attributes_path, 
        pathlib.Path.cwd() / 'token.json', 
        pathlib.Path.cwd() / 'credentials.json')
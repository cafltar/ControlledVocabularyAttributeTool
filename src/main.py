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
    path_to_credentials,
    shouldGenerateReferenceSheet = False):
    print("Main")
    """Entry point of the program. Orchestrates the creation of Google Sheets based attribute tools and writes them to the root of user's Google Drive"""

    # Last column with site-specific information (like SiteVariableName)
    SPREADSHEET_SITE_COL_END = 4
    
    # Column were attributes are to be appended to
    SPREADSHEET_ATTRIBUTE_COL_START = 8
    
    # Column name that contains the controlled variables - used to look up matching attributes
    CONTROLLED_VARIABLE_COL_NAME = 'ControlledVariable'

    # Read soil-specific data inventory (also does some cleaning) <-- code smell!
    reader = inventory_reader.InventoryReader()
    inventory = reader.read_inventory(path_to_inventory)

    # Fill na's with blanks
    inventory.fillna('', inplace=True)

    # Read attributes file and get a dictionary of attributes corresponding to each controlled variable
    attrib_reader = attribute_reader.AttributeReader()
    attributes_df, attributes_dict, attribute_cols = attrib_reader.read_attribute_file(path_to_attributes)

    # Write a Spreadsheet for each site
    writer = google_sheets_io.GoogleSheetsIO(
        path_to_token, 
        path_to_credentials)

    if(shouldGenerateReferenceSheet):
        controlled_df = attributes_df[[
            'GeneralCategory',
            'ControlledVariable',
            'ControlledDescription',
            'Units']]
        controlled_df.fillna('', inplace=True)
    
        create_attribute_sheet(
            writer, 
            controlled_df,
            len(controlled_df.columns),
            len(controlled_df.columns),
            attributes_dict,
            attribute_cols,
            'Reference',
            185,
            100,
            CONTROLLED_VARIABLE_COL_NAME)

    site_ids = inventory["LTARSiteCode"].unique()

    # !!! temp !!!
    site_ids = ['PRHPA']
    # !!!!!!!!!!!!

    spreadsheetIds = []
    for site_id in site_ids:
        site_inventory = inventory[inventory["LTARSiteCode"] == site_id].reset_index(drop=True)

        spreadsheetId = create_attribute_sheet(
            writer,
            site_inventory,
            SPREADSHEET_SITE_COL_END,
            SPREADSHEET_ATTRIBUTE_COL_START,
            attributes_dict,
            attribute_cols,
            site_id,
            185,
            90,
            CONTROLLED_VARIABLE_COL_NAME)

        print(f"Created spreadsheet: {spreadsheetId}")

        spreadsheetIds.append(spreadsheetId)

def create_attribute_sheet(
    writer:google_sheets_io.GoogleSheetsIO,
    df:pd.DataFrame,
    site_data_end_col_num,
    attribute_insert_col_num,
    attributes_dict,
    attribute_cols,
    site_id,
    attrib_col_width: int,
    default_col_width: int,
    controlled_var_header_name = 'ControlledVariable'):

    spreadsheetId = writer.create_sheet(
            f'Attributes_{site_id}',
            df)
    
    # Add attribute columns
    writer.add_columns(
        spreadsheetId, 
        attribute_insert_col_num, 
        len(attribute_cols))

    # Add headers for attribute columns
    writer.add_column_names(
        spreadsheetId,
        0,
        attribute_insert_col_num,
        attribute_cols
    )
    
    # Add inputs
    controlled_var_col = df[controlled_var_header_name]
    for index, value in controlled_var_col.items():
        if value:
            attrib = attributes_dict.get(value)
            if attrib:
                writer.create_inputs(
                    spreadsheetId,
                    attrib, 
                    index+1,                            #+1 for header
                    attribute_insert_col_num)   

    # Format the document
    writer.add_formatting(
        spreadsheetId,
        site_data_end_col_num,
        attribute_insert_col_num, 
        len(attribute_cols),
        attrib_col_width,
        default_col_width)

    return spreadsheetId

if __name__ == '__main__':
    inventory_path = pathlib.Path.cwd() / 'data' / 'input' / 'LtarSoilDataInventory_20220331edits - LtarSoilDataInventory_1020edits.csv'
    attributes_path = pathlib.Path.cwd() / 'data' / 'input' / 'SoilControlledVocabCodedAttrib_20220207.csv'

    main(
        inventory_path,
        attributes_path, 
        pathlib.Path.cwd() / 'token.json', 
        pathlib.Path.cwd() / 'credentials.json',
        False)
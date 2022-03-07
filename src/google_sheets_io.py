from urllib import request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import os.path

import pandas as pd

import controlled_variable_attributes

class GoogleSheetsIO:
    """Handles input and output operations for Google Sheets
    """

    def __init__(self, path_to_token:str, path_to_credentials:str):
        self.__initialize_sheets_api(path_to_token, path_to_credentials)

    def __initialize_sheets_api(self, path_to_token, path_to_credentials):
        """Initializes the sheets api and sets sheets service; sets scope and prepares auth
        """

        # If modifying these scopes, delete the file token.json.
        # Scopes: https://developers.google.com/sheets/api/guides/authorizing
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(path_to_token):
            creds = Credentials.from_authorized_user_file(path_to_token, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    path_to_credentials, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(path_to_token, 'w') as token:
                token.write(creds.to_json())

        self.service = build('sheets', 'v4', credentials=creds)


    
    def create_sheet(self, sheet_name:str, df:pd.DataFrame):
        """Creates a Google Spreadsheet from input dataframe.
        Returns SpreadsheetId
        """
        
        # Create sheet
        create_body = {
            'properties': {
                'title': sheet_name
            }
        }

        spreadsheet = self.service.spreadsheets().create(
            body = create_body,
            fields = 'spreadsheetId'
        ).execute()

        spreadsheetId = spreadsheet.get('spreadsheetId')

        # Add data

        # Transform the DataFrame into a 2D array
        values = [df.columns.values.tolist()]
        values.extend(df.values.tolist())

        data = [{
            'range': "Sheet1",
            'values': values
        }]

        request_body = {
            'value_input_option': 'RAW',
            'data': data
        }

        response = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId = spreadsheetId,
            body = request_body
        ).execute()

        return spreadsheet.get('spreadsheetId')


    def add_columns(self, spreadsheetId:str, start_index:int, num_cols:int):
        """Adds num_cols blank columns to spreadsheetId starting with start_index. Returns Sheets API response
        """
        
        request_body = {
            'requests': [{
                'insertDimension': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': start_index,
                    'endIndex': start_index + num_cols
                },
                'inheritFromBefore': True
            }
            }]
        }

        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId = spreadsheetId,
            body = request_body
        ).execute()

        return response

    def add_column_names(self, spreadsheetId:str, row_num:int, col_num:int, headers:list):
        """Writes column headers at row_num to spreadsheetId starting with col_num for all string values in headers. Returns Sheets API response
        """

        requests = []
        curr_col = col_num

        for header in headers:
            requests.append(
                self.__set_cell_string(
                    header, 
                    0, 
                    row_num, 
                    curr_col)
            )

            curr_col += 1

        body = {
            'requests': requests
        }

        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId = spreadsheetId,
            body = body
        ).execute()

        return response

    def create_inputs(
        self, 
        spreadsheetId,
        controlled_variable_attributes, 
        row_num,
        col_num):
        """Writes input values corresponding to attributes to spreadsheetId

        :param spreadsheetId: spreadsheetId to write to
        :param controlled_variable_attributes: List of attributes belonging to controlled variable term
        :param row_num: row number where values are written to
        :param col_num: starting column number where values are written to, this increments until all attributes are written
        :rtype: Google Sheets API response
        """
        
        requests = []
        curr_col = col_num

        for attribute in controlled_variable_attributes.attributes:
            if not attribute:
                curr_col += 1
                continue

            if attribute.attrib_type == 'Select':
                # Create request for data validation on current cell
                requests.append(self.__create_select_request(
                    attribute,
                    row_num,
                    curr_col
                ))
                # Set the cell value to the attribute's label value
                requests.append(self.__create_select_default_label_request(
                    attribute,
                    row_num,
                    curr_col
                ))
            elif attribute.attrib_type == 'Input':
                requests.append(self.__create_input_request(
                    attribute,
                    row_num,
                    curr_col
                ))
            else:
                raise ValueError(attribute.type)
            
            curr_col += 1

        body = {
            'requests': requests
        }

        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId = spreadsheetId,
            body = body
        ).execute()

        return response

    def add_formatting(
        self, 
        spreadsheetId:str, 
        last_site_field_col:int,
        first_attrib_col:int, 
        num_attrib_cols:int):
        requests = []
        
        requests.append(self.__add_vertical_borders(first_attrib_col, first_attrib_col+num_attrib_cols, 2))
        requests.append(self.__color_input_cells(first_attrib_col, first_attrib_col+num_attrib_cols))
        requests.append(self.__freeze_cells(1,last_site_field_col)) #1 for header row
        requests.append(self.__format_header_text())
        requests.append(self.__set_word_wrap(0, first_attrib_col+num_attrib_cols))
        requests.append(
            self.__set_col_width(
                182, 
                first_attrib_col, 
                first_attrib_col+num_attrib_cols, 
                2, 
                90))
        requests.append(self.__hide_unused_metadata(first_attrib_col+num_attrib_cols, 99))

        body = {
            'requests': requests
        }
        
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId = spreadsheetId,
            body = body
        ).execute()

        return response
    
    def __add_vertical_borders(
        self,
        start_col:int,
        end_col:int,
        step_col:int):
        """Adds a left vertical border to each column, starting with start_col then at every column after step_col until end_col is reached"""
        
        requests = []

        curr_col = start_col

        while curr_col <= end_col:
            request = {
                'updateBorders': {
                    'range': {
                        'startColumnIndex': curr_col,
                        'endColumnIndex': curr_col+1
                    },
                    'left': {
                        'color': {
                            'red': 0,
                            'blue': 0,
                            'green': 0,
                            'alpha': 1
                        },
                        'style': 'SOLID'
                    }
                }
            }

            requests.append(request)

            curr_col += step_col

        return requests

    def __color_input_cells(
        self,
        start_col:int,
        end_col:int):
        
        request = {
            'addConditionalFormatRule': {
                'rule': {
                    'booleanRule': {
                        'condition': {
                            'type': 'NOT_BLANK'
                        },
                        'format': {
                            'backgroundColor': {
                                'alpha': 1,
                                'red': 217/255,
                                'green': 234/255,
                                'blue': 211/255
                            }
                        }
                    },
                    'ranges': [{
                        'startColumnIndex': start_col,
                        'endColumnIndex': end_col
                    }]
                }   
            }
        }

        return request
    
    def __freeze_cells(
        self,
        row_count:int,
        col_count:int):
        request = {
            'updateSheetProperties': {
                'properties': {
                    'gridProperties': {
                        'frozenRowCount': row_count,
                        'frozenColumnCount': col_count
                    }
                },
                'fields': 'gridProperties.frozenRowCount,gridProperties.frozenColumnCount'
            }
        }

        return request

    def __format_header_text(self):
        request = {
            'repeatCell': {
                'range': {
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': 'true',
                            'underline': 'true'
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat)'
            }
        }

        return request

    def __set_word_wrap(
        self,
        start_col:int,
        end_col:int):
        
        request = {
            'repeatCell': {
                'range': {
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                },
                'cell': {
                    'userEnteredFormat': {
                        'wrapStrategy': 'WRAP'
                    }
                },
                'fields': 'userEnteredFormat.wrapStrategy'
            }
        }

        return request

    def __set_col_width(
        self,
        col_width_pixel:int,
        start_col:int,
        end_col:int,
        step_col:int,
        standard_width_pixel:int = None):
        """Sets width of columns to col_width_pixel, starting with start_col then at every column after step_col until end_col is reached. If standard_width_pixel is defined, sets all other columns, from 0 to end_col, to that width"""
        requests = []

        if standard_width_pixel is not None:
            request = {
                'updateDimensionProperties': {
                    'range': {
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': end_col
                    },
                    'properties': {
                        'pixelSize': standard_width_pixel
                    },
                    'fields': 'pixelSize'
                }
            }

            requests.append(request)

        curr_col = start_col

        while curr_col <= end_col:
            request = {
                'updateDimensionProperties': {
                    'range': {
                        'dimension': 'COLUMNS',
                        'startIndex': curr_col,
                        'endIndex': curr_col+1
                    },
                    'properties': {
                        'pixelSize': col_width_pixel
                    },
                    'fields': 'pixelSize'
                }
            }

            requests.append(request)

            curr_col += step_col

        return requests

    def __hide_unused_metadata(
        self,
        start_col:int,
        end_col:int):

        request = {
            'repeatCell': {
                'range': {
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'foregroundColor': {
                                'alpha': 1,
                                'red': 217/255,
                                'green': 217/255,
                                'blue': 217/255
                            }
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat)'
            }
        }

        return request


    def __get_select_label(self, attribute):
        return f'--- {attribute.label} ---'

    def __set_cell_string(
        self, 
        value:str, 
        sheet_id:int, 
        row_num:int, 
        col_num:int):

        request = {
            'updateCells': {
                'rows': [
                    {
                        'values': [{'userEnteredValue': {'stringValue': value}}]
                    }
                ],
                'fields': 'userEnteredValue',
                'start': {
                    'sheetId': sheet_id,
                    'rowIndex': row_num,
                    'columnIndex': col_num
                }
            }
        }

        return request
    
    def __create_select_request(self, attribute, row_num, col_num):
        label = self.__get_select_label(attribute)

        options = []
        options.append({'userEnteredValue': label})
        for item in attribute.values:
            options.append({'userEnteredValue':item})
        
        request = {
            'setDataValidation': {
                'range': {
                    'startRowIndex': row_num,
                    'endRowIndex': row_num+1,
                    'startColumnIndex': col_num,
                    'endColumnIndex': col_num+1
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': options
                    },
                    'inputMessage': f'Select: {attribute.label}',
                    'strict': True,
                    'showCustomUi': True
                }
            }
        }

        return request

    def __create_select_default_label_request(self, attribute, row_num, col_num):
        label = self.__get_select_label(attribute)

        request = self.__set_cell_string(label, 0, row_num, col_num)

        return request
    

    def __create_input_request(self, attribute, row_num, col_num):
        
        label = f'[ {attribute.label} ]'

        request = self.__set_cell_string(label, 0, row_num, col_num)

        return request

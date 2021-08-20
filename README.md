# README

## Purpose

Code to automate the creation of "attribute feedback tools". These tools are basically Google Sheets with dropdown menus. The scripts require a LTAR Data Inventory file with columns for controlled vocabularies and a Controlled Vocabulary Attributes file that defines meaninful information needed associated with the controlled variable term. The attributes are defined in a coded language such that {Input type}|{Label}|[{"list","of","options"}] where,

* {Input type}: required, can be "Select" or "Input"
* {Label}: optional, can have spaces and written in a Sheet with a string value indicating it's an input field (e.g. "My label" = "[ My Label ]"). If left blank then no value is written (e.g. "Input|" = "")
* {"list","of","options"}: optional, no spaces between items, items must be in quotes. Values are used in a dropdown menu via Sheets validation

For example:

* `Select|My label|["Option1","Option2","Option3"]`
* `Input|`
* `Input|Specify your name`

Contact author if you want to use these scripts, basically. Documentation is poor.
## Requirements

A Google Cloud Platform account is required with Google Sheets API enabled and OAuth consent. See here for more details: https://developers.google.com/sheets/api/quickstart/python.

See [requirements.txt](requirements.txt) for more information on required Google libraries

## Running

[src\main.py](src\main.py) is the entry to the script. Variables `inventory_path` and `attributes_path` need to be defined in the `if __name__ == '__main__':` block. These correspond to the path to the LTAR Inventory and Controlled Vocabulary Attribute files, respectively.

## License

As a work of the United States government, this project is in the public domain within the United States.

Additionally, we waive copyright and related rights in the work worldwide through the CC0 1.0 Universal public domain dedication.

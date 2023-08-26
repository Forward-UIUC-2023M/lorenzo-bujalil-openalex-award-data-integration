"""
Module: load_raw_awards.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Main script to call helper scripts to create the database, 
load data, and insert the data into the new database.

Dependencies:
- pandas
- sys
"""

import sys
sys.path.append('helper_scripts')
import pandas as pd
from xml_to_sqlite import create_database,parseXML


def getRawData(xml_path):
    """
    Retrieves raw data from xml file,
    and inserts them into sqlite database.

    Parameters:
    xml_path : string
               Path to the source xml file.

    Returns:
    list
        A list of awards that have been retrieved from xml file.
    """
    print("Getting award path...")
    awards = parseXML(xml_path)
    print("Done getting path!\n")
    return awards


if __name__ == "__main__":
    create_database() # Initially creating a local sqlite database to be able to quickly access records
    xml_path = 'source/awards-20230530.xml' # Path to xml file
    awards = getRawData(xml_path) # Function calls the helper parseXML function to initally retrieve records and insert them into the created database
    
    

    
    


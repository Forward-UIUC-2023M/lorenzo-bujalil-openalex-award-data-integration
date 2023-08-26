"""
Module: xml_to_sqlite.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Create a database for award data, parse xml file, and insert data into database.

Dependencies:
- lxml
- sqlite
"""

from lxml import etreea
import sqlite3
database_file = "data/sqlite/awards.db"

def create_database():
    """
    Creates database to store award data.

    Parameters:
    None

    Returns:
    None
    """
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    # Uncomment to do a full reload
    # cursor.execute('''DROP TABLE awards
    # ''')
    
    # Currently database has most essential elements.
    cursor.execute('''CREATE TABLE IF NOT EXISTS awards (
                        award_id INTEGER PRIMARY KEY,
                        principal_investigators TEXT,
                        recipients TEXT
                    )''')

    conn.commit()
    conn.close()

def insert_data(row_data):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO awards (award_id,principal_investigators,recipients) VALUES (?,?,?)", (row_data['id'],row_data['principal_investigators'],row_data['recipients']))

    conn.commit()
    conn.close()



def parseXML(xml_path):
    """
    Accesses all of the award records within the source xml file.
    Uses the lxml package to be able to handle the 2 million records.
    
    Parameters:
    xml_path: string
              Path to xml file.
    
    Returns:
    List
        List of the parsed awards.
    """
    context = etree.iterparse(xml_path, events=('end',), tag='award')
    num_awards = 0

    awards = []
    for event, element in context:
        row_data = {}
        
        for child in element.iterchildren():
            
            tag = child.tag
            text = child.text
            row_data[tag] = text
        id_attribute = element.attrib.get('id')
        row_data['id'] = id_attribute
        
        awards.append(row_data)

        insert_data(row_data)

        element.clear()

        
        while element.getprevious() is not None:
            del element.getparent()[0]
        print(num_awards)
        num_awards+=1

    del context

    return awards




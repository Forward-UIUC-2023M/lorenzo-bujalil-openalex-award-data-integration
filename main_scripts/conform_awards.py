"""
Module: conform_awards.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Main script to call helper scripts to create the database, 
load data, and insert the data into the new database.

Dependencies:
- pandas
- time
- csv
- sys
"""

import sys
sys.path.append('helper_scripts')
import time
from query_sqlite_db import get_data,establish_conn,close_conn,read_data,regexp
from normalize import clean_author_data
import csv
import pandas as pd

def write_query_to_output(path,res):
    """
    Opens up the file and writes out any list of information

    Parameters:
    path : string
            Path name for file
    res : List
            List of data to write

    Returns:
    None
    """
    with open(path,'w') as f:
        for author in res:
            if author[0] == None:
                continue
            f.write(author[0]+'\n')

def write_clean_data_to_text(path,data):
    """
    Opens up the text file and writes out any list of information

    Parameters:
    path : string
            Path name for file
    data : List
            List of data to write

    Returns:
    None
    """
    with open(path,'w') as f:
        for author in data:
            # if author == None:
            #     continue
            f.write(author+'\n')

def write_data_to_csv(path,data,column_name):
    """
    Opens up the csv file and writes out any list of information

    Parameters:
    path : string
            Path name for file
    data : List
            List of data to write
    column_name : string
            Name of column for data in csv file

    Returns:
    None
    """
    with open(path,'w',newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([column_name])
        for value in data:
            writer.writerow([value])

def append_column(path,data,column_name):
    """
    Appends column to a csv file

    Parameters:
    path : string
            Path name for file
    data : List
            List of data to write
    column_name : string
            Name of column for data in csv file
    
    Returns:
    None
    """
    df = pd.read_csv(path)
    df[column_name] = data
    df.to_csv(path,index=False)

if __name__ == "__main__":
    query = '''SELECT principal_investigators FROM awards''' # Pull all of the authors from the sqlite database
    conn = establish_conn() # Create a connection with the sqlite database
    conn.create_function("REGEXP", 2, regexp) # Create a regex function for complex queries
    res = get_data(conn,query,'') # Retrieve data from the sqlite database using the above query
    raw_data = res.fetchall() # Retrieve all the data from the result
    raw_data_list = [] # Create a list to store the raw data
    for data in raw_data: # Load the list with the raw data
        raw_data_list.append(data[0])

    print(f'Size of raw data:{len(raw_data)}') # Total amount of raw data 

    # Prints the number of authors remaining to clean
    print("Remaining authors: ", read_data(conn,'''SELECT count(principal_investigators) 
                                                FROM awards 
                                                WHERE principal_investigators NOT LIKE '%Contact PI / Project Leader: %' 
                                                AND principal_investigators NOT LIKE 'Name:%' 
                                                AND principal_investigators NOT LIKE 'None' 
                                                AND principal_investigators NOT LIKE 'Phone:%' 
                                                AND principal_investigators NOT LIKE '%(Principal Investigator)%'
                                                AND principal_investigators NOT LIKE '%(Former Principal Investigator)%'
                                                AND principal_investigators NOT REGEXP ?''', (r'\b[A-Za-z]+\s+(?<!\n)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\r?\n?',))) 
    clean_authors = [] # Create an empty list of authors to store the clean authors
    clean_authors_idx = [] # Stores the index of the clean authors
    null_values = 0 # Counts the number of null values that appear in the award data
    none_authors = 0 # Counts the number of records that have no principal investigators in the award data
    phone_numbers = 0 # Counts the number of records that have only a phone number as the principal investigator in the award data

    for idx,author in enumerate(raw_data): # Iterate through the raw data and run the cleaning function found in the normalization helper script
        if author[0] != None and author[0].startswith('Phone:'):
            phone_numbers+=1
            continue
        if author[0] == 'None':
            none_authors+=1
            continue
        if author[0] != None:
            clean_authors_count = len(clean_authors)
            clean_author_data(author[0],clean_authors)
            if clean_authors_count == len(clean_authors)-1:
                clean_authors_idx.append(idx)
        else:
            null_values+=1

    # Print statements to retrieve current data information
    print(f'Null Values: {null_values}')
    print(f'None Authors: {none_authors}')
    print(f'Phone Numbers: {phone_numbers}')
    print(f'Current Clean Number of authors : {len(clean_authors)}')

    # Write the clean authors to a text file
    write_clean_data_to_text('data/conformed/awards/clean_authors.txt',clean_authors)
    # Write the clean authors to a csv file
    write_data_to_csv('data/conformed/awards/clean_authors.csv',clean_authors,'primary_investigator')
    # Write the raw data to a text file
    write_query_to_output('data/conformed/awards/raw_data.txt',raw_data)
    # Write the raw data to a csv file
    write_data_to_csv('data/conformed/awards/raw_data.csv',raw_data_list,'primary_investigator')

    # Retrieve the data of the remaining authors
    remaining_authors = get_data(conn,'''SELECT principal_investigators 
                                        FROM awards 
                                        WHERE principal_investigators NOT LIKE '%Contact PI / Project Leader: %' 
                                        AND principal_investigators NOT LIKE 'Name:%' 
                                        AND principal_investigators NOT LIKE 'None'
                                        AND principal_investigators NOT LIKE 'Phone:%' 
                                        AND principal_investigators NOT LIKE '%(Principal Investigator)%'
                                        AND principal_investigators NOT LIKE '%(Former Principal Investigator)%'
                                        AND principal_investigators NOT REGEXP ?''', (r'\b[A-Za-z]+\s+(?<!\n)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\r?\n?',)).fetchall()
    
    # Write the data from the remaining authors to a text file
    write_query_to_output('data/conformed/awards/remaining_authors.txt',remaining_authors)
    
    # Get the data of the institutions from the award
    insitutions = get_data(conn,'''SELECT recipients FROM awards''','').fetchall()
    insitutions_list = [] # Create a list to store the institutions
    for inst in insitutions: # Iterate through the result and add the data to the list of institutions
        insitutions_list.append(inst[0])

    # write the data of the raw institutions to a text file
    write_query_to_output('data/conformed/awards/institutions/raw_data.txt',insitutions)

    # add a column to the raw data of the institutions
    append_column('data/conformed/awards/raw_data.csv',insitutions_list,'insitutions')

    # create a list of institutions based on the values in the clean authors idx
    insitutions_list = [insitutions_list[idx] for idx in clean_authors_idx]
    print(len(insitutions_list)) # number of institutions
    # Append the institution column to the clean authors csv file
    append_column('data/conformed/awards/clean_authors.csv',insitutions_list,'insitutions') 

    close_conn(conn) # Close the Connection


    
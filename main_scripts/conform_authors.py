"""
Module: conform_authors.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Main script used to clean up institution data currently found in
the postgres database. This is done to create a new database
that has the full name written out in the database.

Dependencies:
- pandas
- time
- datetime
- email
- csv
- sys
- requests
"""

import sys
sys.path.append('helper_scripts')
import requests
from connect_to_postgres import setPostgresConnection,close_conn
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import pandas as pd
import csv

def replace_institution_name(insert_names,create_table,truncate_table):
    """
    Retrieve data from the postgreSQL database then replace the institution
    url with the name by using the requests library and the openalex api. 
    Send a request and get the data required for that institution. In this 
    data is the name of the institution and it can be used to replace url.

    Parameters:
    insert_names : bool
        Insert names into the new table.
    create_table : bool
        Create a new table to store the new column
    truncate_table : bool
        Remove all the data from the created table before loading more
    Returns:
    None
    """
    
    conn = setPostgresConnection()
    cur = conn.cursor()
    print("Getting Rows")
    
    cur.execute('''
                SELECT id,last_known_institution
                FROM openalex.authors_partition
                ORDER BY last_known_institution
                LIMIT 10000000;
                ''')

    
    rows = cur.fetchall()
    print("Rows Attained")
    visited_inst = {}

    inst_names = []
    inst_names_csv = []
    
    df = pd.read_csv('data/conformed/authors/visited_cleaned_names.csv')
    


    prev_visited = {institution: other_value for institution, other_value in zip(df['last_known_institution'], df['last_known_institution_name'])}

    print("Changing name")
    base_url = 'https://api.openalex.org/institutions/'

    with requests.Session() as session:  # Use a session to reuse connection
        for i, row in enumerate(rows):

            institution = row[1]
            id = row[0]
            if institution in prev_visited:
                inst_names.append([id,prev_visited[institution]])
                continue

            if institution is None:
                inst_names.append([id, institution])

                # inst_names_csv.append({'idx':i,'id':id,'last_known_institution_name':institution})
                continue
            if institution not in visited_inst:
                api_url = base_url + institution.replace("https://openalex.org/", "")
                response = session.get(api_url) 
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        retry_date = parsedate_to_datetime(retry_after)
                        wait_seconds = (retry_date - datetime.now(timezone.utc)).total_seconds() + 0.3
                    else:
                        wait_seconds = 10  
                    # print(f"Rate limit exceeded. Retrying in {wait_seconds} seconds.")
                    time.sleep(wait_seconds)
                    response = session.get(api_url)

                response.raise_for_status()

                institution_name = response.json().get("display_name")
                visited_inst[institution] = institution_name
                inst_names.append([id, institution_name])
                inst_names_csv.append({'idx':i,'last_known_institution':institution,'last_known_institution_name':institution_name})
            else:
                inst_names.append([id, visited_inst[institution]])
                # inst_names_csv.append({'idx':i,'id':id,'last_known_institution_name':visited_inst[institution]})

    new_rows = pd.DataFrame(inst_names_csv)
    df = pd.concat([df, new_rows], ignore_index=True)
    df.to_csv('data/conformed/authors/visited_cleaned_names.csv', index=False)

    if truncate_table:
        cur.execute("""
                    TRUNCATE TABLE openalex.institution_dimension_2;
                    """)
        conn.commit()

    if create_table:
        cur.execute("""
            
            CREATE TABLE IF NOT EXISTS openalex.institution_dimension_2(
                id TEXT PRIMARY KEY,
                last_known_institution_name TEXT
            );
                    
            ALTER TABLE IF EXISTS openalex.institution_dimension_2
            OWNER to pzl2;
        """)
        conn.commit()

    if insert_names:
        insert_df = pd.read_csv('data/conformed/authors/insert_names.csv')
        print("Inserting names")
        insert_names_list = []
        for idx,row in enumerate(inst_names):
            if row[1] == None:
                insert_names_list.append({'id':row[0],'last_known_institution_name':'null'})
            else:
                insert_names_list.append({'id':row[0],'last_known_institution_name':row[1]})
            
        insert_df = pd.concat([insert_df,pd.DataFrame(insert_names_list)],ignore_index=True)
        insert_df.to_csv('data/conformed/authors/insert_names.csv')

        # Regex Expression to Remove Numbers : (?<=\n)\d+,


    print("Done")
    

    close_conn(cur,conn)
    


if __name__ == "__main__":
    replace_institution_name(True,False,False)
"""
Module: query_sqlite_db.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Helper functions required to connect/query sqlite database.

Dependencies:
- time
- sqlite
- re
"""

import sqlite3
import time
import re
database_file = "data/sqlite/awards.db"

def establish_conn():
    """
    Establishes a connection to sqlite database.

    Parameters:
    None
    
    Returns:
    Sqlite Connection Object
        The connection tool used to access database.
    """
    conn = sqlite3.connect(database_file)
    return conn

def get_data(conn,query,regex):
    """
    Retrieves data from the sqlite database.

    Parameters:
    conn : Sqlite Connection Object
        The connection tool used to access database.
    query : string
        String containing the query to retrieve data.
    regex : string
        Regex pattern used to query data.
    
    Returns:
    Sqlite Cursor Object
        Cursor can be used to retrieve or navigate data.
    """
    start_time = time.time()
    cursor = conn.cursor()
    if regex == '':

        res = cursor.execute(query)
    else:
        res = cursor.execute(query,regex)
        
    end_time = time.time()
    conn.commit()
    # print(f'{1000*(end_time-start_time)} ms') # Uncomment to check time elapsed
    return res

def read_data(conn,query,regex):
    """
    Retrieves data from the sqlite database.

    Parameters:
    conn : Sqlite Connection Object
        The connection tool used to access database.
    query : string
        String containing the query to retrieve data.
    regex : string
        Regex pattern used to query data.
    
    Returns:
    List
        List of the queried data.
    """
    start_time = time.time()
    cursor = conn.cursor()
    if regex == '':

        res = cursor.execute(query)
    else:
        res = cursor.execute(query,regex)
        
    row = res.fetchall()
    end_time = time.time()
    conn.commit()
    # print(f'{1000*(end_time-start_time)} ms') # Uncomment to check time elapsed
    return row

def close_conn(conn):
    """
    Closes connection to database.

    Parameters:
    conn : Sqlite Connection Object

    Returns:
    None
    """
    conn.close()

def regexp(expr, item):
    """
    Regex function used for complex search results.

    Parameters:
    expr : string
        Regular Expression.
    item : string
        Item to find.
    
    Returns:
    bool
        True if regular expression finds a match, else False.
    """
    reg = re.compile(expr)
    return reg.search(item) is not None


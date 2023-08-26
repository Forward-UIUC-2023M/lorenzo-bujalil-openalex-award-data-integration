"""
Module: connect_to_postgres.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Helper script to create connection to PostgreSQL database.

Dependencies:
- psycopg2
"""

import psycopg2

def setPostgresConnection():
    """
    Sets up connection to PostgreSQL server.
    
    Parameters:
    None 

    Returns:
    PostgreSQL Connection Object
    """
    db_params = {
        "host": "Hawk5.csl.illinois.edu",
        "port": 5432,  
        "database": "postgres",
        "user": "pzl2",   
        "password": "postgres"
    }

    conn = psycopg2.connect(**db_params)
    return conn

def close_conn(cur,conn):
    """
    Closes connection to PostgreSQL server.
    
    Parameters:
    cur : PostgreSQL Cursor Object
        Cursor for PostgreSQL
    conn : PostgreSQL Connection Object
        Connection for PostgreSQL 

    Returns:
    None
    """
    cur.close()
    conn.close()
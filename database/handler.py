import mysql.connector
from flask import current_app, g

def connect_db():
    config = current_app.config['DB_CONFIG']
    
    db_config = {
        'host': config['host'],
        'user': config['user'],
        'password': config['password'],
        'database': config['database']
    }
    
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"FATAL DATABASE ERROR: Could not connect to the database. Error: {err}")
        raise RuntimeError("Database connection failed.") from err

def get_db_connection_for_request():
    if 'db' not in g:
        g.db = connect_db()
    return g.db

def execute_query(sql, params=None, fetch_one=False):
    conn = get_db_connection_for_request()
    
    cursor = conn.cursor(dictionary=True) 
    
    try:
        cursor.execute(sql, params or ())
        
        if sql.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            return result
        
        conn.commit()
        return cursor.rowcount 
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"SQL Error executing query: {sql} with params {params}. Error: {err}")
        raise err
    finally:
        cursor.close()

def insert_data(table_name, data):
    columns = ', '.join(data.keys())
    # Use '%s' as the placeholder for mysql.connector
    placeholders = ', '.join(['%s'] * len(data))
    values = list(data.values())
    
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    return execute_query(sql, values)

# NOTE: The get_db_connection_for_request and execute_query 
# functions must be imported into app.py and routes/*.py.
import sqlite3      
import os       
from typing import Optional

# Function to inspect schema
def inspect_schema(db_path: str) -> dict:   
    """
    Inspects a SQLite database and returns complete
    schema information including tables, columns,
    primary keys, foreign keys, and row counts. 
    """
    conn = sqlite3.connect(db_path)     # opens a connection to the SQLite database  at db_path.
    cursor = conn.cursor()      # Creates the Cursor object to execute SQL queries.

    cursor.execute(     # Executing an SQL query.
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )

    tables = [row[0] for row in cursor.fetchall()]  
    """  
    Stores all table names in the tables list and Extract the first element (name) from every row.
    """  

    schema = {
        "tables": {},
        "relationships": [],
        "ambiguous_columns": {}
    }

    all_columns = {}

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")   # Retrieves column information for the current table.
        columns_info = cursor.fetchall()    # Stores all column metadata.

        cursor.execute(f"PRAGMA foriegn_key_list({table})")     # Retrieves foreign key information.
        fk_info = cursor.fetchall()     # Stores foreign key metadata.

        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        row_count = cursor.fetchone()[0]

        columns = []
        pk_columns = []     # Lists to store primary key columns.

        for col in columns_info:
            col_name = col[1]   # Gets the column name.
            col_type = col[2]   # Gets the column data type.
            is_pk = col[5] > 0  # Checks whether the column is a primary key.
            not_null = col[3] == 1  # Checks whether the column is NOT NULL.

            columns.append({    # Append the above informations in the columns list as dictionary.
                "name": col_name,
                "type": col_type,
                "is_pk": is_pk,
                "not_null": not_null
            })

            if is_pk:
                pk_columns.append(col_name)     # Add the column name to the primary key list, if it is primary key.

            if col_name not in all_columns:     # Checks if this column name has been seen before.
                all_columns[col_name] = []
            all_columns[col_name].append(table)     # Adds the current table name to the list.

        foreign_keys = []    # Lists to store foreign_keys
        for fk in fk_info:

            fk_dict = {
                "from_column": fk[3],   # Stores the source column.
                "to_table": fk[2],      # Stores the referenced table.
                "to_column": fk[4]      # Stores the referenced column.
            }

            foreign_keys.append(fk_dict)    # Adds the above dic to the list
            schema["relationships"].append(
                f"{table}.{fk[3]} -> {fk[2]}.{fk[4]}"
            )

        # Now, saving the table information
        schema["tables"][table] = {     # Creates an entry for the current table.
            "columns": columns,
            "primary_keys": pk_columns,
            "foreign_keys": foreign_keys,
            "row_count": row_count
        }

    # Find ambigious columns - same name in multiple tables
    for col_name, table_list in all_columns.items():
        if len(table_list) > 1:     # Checks if the column exists in more than one table.
            schema["ambiguous_columns"][col_name] = table_list      # Saves that column as ambiguous.

    conn.close()    # Closes the database connection.
    return schema   # returns the completed schema dictionary.


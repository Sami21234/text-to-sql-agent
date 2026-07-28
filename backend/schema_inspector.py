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

# Now, function to generate prompt
def generate_prompt(schema: dict, question: str) -> str:
    """
    Generates a precise SQL prompt from inspected schema.
    Rules are derived from actual database structure -
    no hardcoding needed.
    """

    # Getting the desired dictionaries
    tables = schema["tables"]
    relationships = schema["relationships"]
    ambiguous = schema["ambiguous_columns"]

    # Build table descriptions
    table_lines = []    # Creates a list for table descriptions.
    for table_name, info in tables.items():
        col_descriptions = []       # Lists of colmn description.
        for col in info["columns"]:
            desc = col["name"]
            if col["is_pk"]:
                desc += " (PK)"     # if the column is primmary key, then append " (PK)" in the column name
            col_descriptions.append(desc)       # stores  description.

        fk_descriptions = []     # Lists of foreign key descriptions.
        for fk in info["foreign_keys"]:
            fk_descriptions.append(
                f"{fk['from_column']} → "
                f"{fk['to_table']}.{fk['to_column']}"
            )

        line = (    # building the table description.
            f"Table: {table_name} "
            f"({info['row_count']} rows)\n"
            f"  Columns: {', '.join(col_descriptions)}"
        )
        if fk_descriptions:
            line += (
                f"\n  Foreign keys: "
                f"{', '.join(fk_descriptions)}"
            )
        table_lines.append(line)

    # Auto-generate disambiguation rules
    disambiguation_rules = []   # Lists of abmiguity rules.
    for col_name, table_list in ambiguous.items():
        for tbl in table_list:
            disambiguation_rules.append(
                f"Write {tbl}.{col_name} not just {col_name}"
            )

    prompt = f"""You are a SQLite expert. Write a single SQL query to answer the question.

DATABASE SCHEMA:
{chr(10).join(table_lines)}

RELATIONSHIPS:
{chr(10).join(relationships) if relationships else "None"}

DISAMBIGUATION RULES:
{chr(10).join(disambiguation_rules) if disambiguation_rules else "No ambiguous columns"}

STRICT RULES:
- Return ONLY raw SQL — no markdown, no backticks, no explanation
- SQLite syntax only — use strftime() not MONTH() or YEAR()
- Exactly ONE SELECT statement
- UPPERCASE for status/enum values
- COUNT(*) for counting rows, SUM() for monetary totals
- Always prefix ambiguous column names with table name
- JOIN using the foreign key relationships listed above

QUESTION: {question}

SQL:"""

    return prompt


# Now, function to generate the Sample_Questions

def generate_sample_questions(
        schema: dict,
        llm,
        count: int = 10     # number of questions.
) -> list[str]:
    """
    Uses the LLM to generate relevant sample questions
    based on actual database schema.
    """
    tables = schema["tables"]

    table_summary = []
    for table_name, info in tables.items():
        col_names = [col["name"] for col in info["columns"]]
        table_summary.append(
            f"{table_name}: {', '.join(col_names)}"
        )

    prompt = f"""You are helping users explore a database.
Based on this database schema, generate exactly {count} 
useful analytical questions a business user would ask.

SCHEMA:
{chr(10).join(table_summary)}

Return exactly {count} questions, one per line.
No numbering, no bullets, no explanation.
Only the questions themselves.
Make them specific to the actual table and column names."""

    response = llm.invoke(prompt)
    lines = [    # building the output list.
        line.strip()
        for line in str(response).strip().split('\n')
        if line.strip() and '?' in line     # Keeps only non-empty lines containing a question mark.
    ]
    return lines[:count]

# Now, function to validate_sqlite_file
def validate_sqlite_file(file_bytes: bytes) -> tuple[bool, str]:
    """
    Validates that uploaded file is a genuine SQLite database.
    Checks magic bytes - cannot be faked by renaming a file.
    """
    # SQLite files always start with this exact string
    
# It is used as connection manager to the database 
import sqlite3  
import os

DB_PATH = os.path.join(   # creating a path to the database file  
    os.path.dirname(__file__),
    "food_delivery.db"
)

# Function to get the path to the database file
def get_db_path():
    """ Returns the path to the database file."""
    return DB_PATH  

# Function to verify the connection to the database
def verify_connection():
    """ Verifies the database exists and is readable. Called on startup to catch missing DB early."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}. " f"Run create_db.py to create the database first.")
    conn = sqlite3.connect(DB_PATH)     # Establishing a connection to the database
    cursor = conn.cursor()                 # Creating a cursor object to interact with the database
    cursor.execute("SELECT COUNT(*) FROM orders")  # Executing a simple query to check if the database is readable
    count = cursor.fetchone()[0]  # Fetching the count of orders
    conn.close()  # Closing the connection to the database
    print(f"[DB] Connected. {count} orders in database.")  # Printing the number of orders in the database
    return True  # Returning True to indicate that the connection was successful
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "backend/food_delivery.db"

# Now, Seeding Data

CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Surat", "Pune", "Jaipur"]

RESTAURANTS = [
    ("Spice Garden",        "Indian",     "Mumbai",    4.5),
    ("Burger Barn",         "American",   "Delhi",     4.1),
    ("Wok Express",         "Chinese",    "Bangalore", 4.3),
    ("Pizza Palace",        "Italian",    "Mumbai",    4.7),
    ("Taco Fiesta",         "Mexican",    "Hyderabad", 3.9),
    ("Sushi Central",       "Japanese",   "Bangalore", 4.6),
    ("Dosa Delight",        "South Indian","Chennai",  4.4),
    ("Kebab Kingdom",       "Middle Eastern","Delhi",  4.2),
    ("Thai Orchid",         "Thai",       "Mumbai",    4.5),
    ("The Burger Lab",      "American",   "Bangalore", 4.0),
]

MENU_ITEMS = {
    "Spice Garden": [
        ("Butter Chicken",    "Main Course", 320),
        ("Biryani",           "Main Course", 280),
        ("Paneer Tikka",      "Starter",     220),
        ("Garlic Naan",       "Bread",        60),
        ("Mango Lassi",       "Beverage",     80),
    ],
    "Burger Barn": [
        ("Classic Burger",    "Burger",      180),
        ("Double Patty",      "Burger",      260),
        ("Crispy Fries",      "Sides",        90),
        ("Onion Rings",       "Sides",       110),
        ("Chocolate Shake",   "Beverage",    150),
    ],
    "Wok Express": [
        ("Kung Pao Chicken",  "Main Course", 290),
        ("Fried Rice",        "Main Course", 180),
        ("Spring Rolls",      "Starter",     140),
        ("Dim Sum",           "Starter",     200),
        ("Green Tea",         "Beverage",     60),
    ],
    "Pizza Palace": [
        ("Margherita Pizza",  "Pizza",       350),
        ("Pepperoni Pizza",   "Pizza",       420),
        ("BBQ Chicken Pizza", "Pizza",       450),
        ("Garlic Bread",      "Sides",       120),
        ("Tiramisu",          "Dessert",     180),
    ],
    "Taco Fiesta": [
        ("Beef Tacos",        "Tacos",       220),
        ("Chicken Burrito",   "Burrito",     280),
        ("Nachos",            "Starter",     160),
        ("Guacamole",         "Sides",        90),
        ("Horchata",          "Beverage",     80),
    ],
    "Sushi Central": [
        ("Salmon Sashimi",    "Sashimi",     480),
        ("Tuna Roll",         "Roll",        320),
        ("Dragon Roll",       "Roll",        380),
        ("Miso Soup",         "Soup",         80),
        ("Matcha Ice Cream",  "Dessert",     150),
    ],
    "Dosa Delight": [
        ("Masala Dosa",       "Main Course", 120),
        ("Idli Sambar",       "Breakfast",    90),
        ("Vada",              "Starter",      60),
        ("Filter Coffee",     "Beverage",     40),
        ("Rava Dosa",         "Main Course", 110),
    ],
    "Kebab Kingdom": [
        ("Seekh Kebab",       "Starter",     280),
        ("Chicken Shawarma",  "Main Course", 220),
        ("Hummus",            "Sides",       120),
        ("Pita Bread",        "Bread",        60),
        ("Mint Lemonade",     "Beverage",     90),
    ],
    "Thai Orchid": [
        ("Pad Thai",          "Main Course", 320),
        ("Green Curry",       "Main Course", 350),
        ("Tom Yum Soup",      "Soup",        180),
        ("Mango Sticky Rice", "Dessert",     160),
        ("Thai Iced Tea",     "Beverage",    100),
    ],
    "The Burger Lab": [
        ("Lab Special Burger","Burger",      320),
        ("Truffle Fries",     "Sides",       160),
        ("Chicken Wings",     "Starter",     240),
        ("Mac and Cheese",    "Sides",       180),
        ("Oreo Shake",        "Beverage",    180),
    ],
}

CUSTOMERS_NAMES = [
    "Mohd Sami", "Ash Ketchum", "Brock", "Gary Oak", "Misty", "Tracey Sketchit", "May", "Dawn",
    "Prof. Oak", "Tony Starc", "Kavya Reddy", "Rohit Gupta",
    "Divya Krishnan", "Amit Joshi", "Pooja Verma", "Karan Malhotra",
    "Riya Desai", "Siddharth Rao", "Meera Pillai", "Aditya Kumar",
    "Anjali Choudhary", "Nikhil Bhatt", "Shreya Saxena", "Varun Tiwari",
    "Nisha Agarwal", "Manish Pandey", "Lakshmi Venkat", "Suresh Bose",
    "Deepa Menon", "Rajesh Khanna", "Sunita Mishra", "Gaurav Chauhan",
    "Pallavi Jain", "Tarun Srivastava",    
]

AGENT_NAMES = [
    "Ravi Kumar", "Suraj Yadav", "Manoj Singh", "Deepak Verma",
    "Ajay Sharma", "Vijay Patel", "Sanjay Gupta", "Ramesh Tiwari",
]

# Function to generate a random date within the last 'days_back' days
def random_date(days_back=90):  # Generate a random date within the last 'days_back' days
    now = datetime.now()    # Get the current date and time
    start = now - timedelta(days=days_back)  # Calculate the start date
    random_seconds = random.randint(0, int((now - start).total_seconds()))  # Generate a random number of seconds within the range

    dt = start + timedelta(seconds=random_seconds)
    # Adding Peak Hours Bias: more orders 12 AM to 2 PM and 6 PM to 9 PM
    if random.random() < 0.4:  # 40% chance to be in peak hours
        hour = random.choice([12, 13, 18, 19, 20]) 
        dt = dt.replace(hour=hour, minute=random.randint(0, 59))    # Random minute within the hour
    return dt.strftime("%Y-%m-%d %H:%M:%S")     # Return the date in a format suitable for SQLite

# Function to create the database and tables
def create_database():
    conn = sqlite3.connect(DB_PATH)     # Connect to the SQLite database (it will create the file if it doesn't exist)
    cursor = conn.cursor()      # Create a cursor object to execute SQL commands

    # Create tables
    cursor.executescript('''   
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS menu_items;
        DROP TABLE IF EXISTS restaurants;
        DROP TABLE IF EXISTS users;
        
        CREATE TABLE users (
           user_id INTEGER PRIMARY KEY AUTOINCREMENT,
           name TEXT NOT NULL,
           email TEXT NOT NULL UNIQUE,
           phone TEXT,
           role TEXT CHECK(role IN ('CUSTOMER', 'RESTAURANT', 'DELIVERGY_AGENT')) NOT NULL,
           city TEXT,
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP              
        );
        
        CREATE TABLE restaurants (
           restaurant_id INTEGER PRIMARY KEY AUTOINCREMENT,
           name TEXT NOT NULL,
           cuisine_type TEXT,
           city TEXT,
           rating REAL DEFAULT 0.0,
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE menu_items (
           item_id INTEGER PRIMARY KEY AUTOINCREMENT,
           restaurant_id INTEGER NOT NULL,
           name TEXT NOT NULL,
           category TEXT,
           price REAL NOT NULL,
           is_available INTEGER DEFAULT 1,
           FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
        );
        
        CREATE TABLE orders (
           order_id INTEGER PRIMARY KEY AUTOINCREMENT,
           customer_id INTEGER NOT NULL,
           restaurant_id INTEGER NOT NULL,
           agent_id INTEGER,
           status TEXT CHECK(status IN ('PLACED', 'IN_PROGRESS', 'DELIVERED', 'CANCELLED')) NOT NULL DEFAULT 'PLACED',
           total_amount REAL NOT NULL,
           delivery_fee REAL DEFAULT 0.0,
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
           delivered_at DATETIME,
           FOREIGN KEY (customer_id) REFERENCES users(user_id), 
           FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id),
           FOREIGN KEY (agent_id) REFERENCES users(user_id)
        );
        
        CREATE TABLE order_items (
           order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
           order_id INTEGER NOT NULL,
           item_id INTEGER NOT NULL,
           quantity INTEGER NOT NULL DEFAULT 1,
           unit_price REAL NOT NULL,
           FOREIGN KEY (order_id) REFERENCES orders(order_id),
           FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
        );
    ''')

    # Insert customers
    customer_ids = []   # List to store customer IDs
    for i, name in enumerate(CUSTOMERS_NAMES):  # Loop through the customer names and insert them into the users table
        email = name.lower().replace(" ", ".") + "@gmail.com"
        city = random.choice(CITIES)
        phone = f"9{random.randint(6000000000, 9999999999)}"
        cursor.execute('''
            INSERT INTO users (name, email, phone, role, city)
            VALUES (?, ?, ?, 'CUSTOMER', ?)
        ''', (name, email, phone, city))
        customer_ids.append(cursor.lastrowid)

    # Insert delivery agents
    agent_ids = []   # List to store agent IDs
    for name in AGENT_NAMES:  # Loop through the agent names and insert them into the users table
        email = name.lower().replace(" ", ".") + "@gmail.com"
        city = random.choice(CITIES)
        phone = f"9{random.randint(6000000000, 9999999999)}"
        cursor.execute('''
            INSERT INTO users (name, email, phone, role, city)
            VALUES (?, ?, ?, 'DELIVERGY_AGENT', ?)
        ''', (name, email, phone, city))
        agent_ids.append(cursor.lastrowid)

    # Insert restaurants 
    restaurant_ids = {}   # Dictionary to store restaurant IDs
    for name, cuisine, city, rating in RESTAURANTS:  # Loop through the restaurant names and insert them into the restaurants table
        cursor.execute('''
            INSERT INTO restaurants (name, cuisine_type, city, rating)
            VALUES (?, ?, ?, ?)
        ''', (name, cuisine, city, rating))
        restaurant_ids[name] = cursor.lastrowid

    # Insert menu items
    item_ids = {}  # Dictionary to store item IDs
    for restaurant_name, items in MENU_ITEMS.items():  # Loop through the menu items
        rest_id = restaurant_ids[restaurant_name]  # Get the restaurant ID for the current restaurant
        item_ids[restaurant_name] = []  # Initialize the list for the current restaurant
        for item_name, category, price in items:  # Loop through the items for the current restaurant
            cursor.execute('''
                INSERT INTO menu_items (restaurant_id, name, category, price)
                VALUES (?, ?, ?, ?)
            ''', (rest_id, item_name, category, price))
            item_ids[restaurant_name].append((cursor.lastrowid, price))  # Store the item ID for the current item

    # Insert orders with realistic distribution
    # More popular restaurants get more orders
    restaurant_weights = [
        ("Pizza Palace",     15),
        ("Spice Garden",     14),
        ("Sushi Central",    12),
        ("Dosa Delight",     11),
        ("Wok Express",      10),
        ("Burger Barn",       9),
        ("Thai Orchid",       9),
        ("Kebab Kingdom",     8),
        ("The Burger Lab",    7),
        ("Taco Fiesta",       5),
    ]

    restaurant_pool = []
    for name, weight in restaurant_weights:  # Create a weighted pool of restaurants based on their popularity
        restaurant_pool.extend([name] * weight)

    # Generate orders
    for _ in range(500):  # Generate 500 orders
        customer_id = random.choice(customer_ids)  # Randomly select a customer
        restaurant_name = random.choice(restaurant_pool)  # Randomly select a restaurant based on
        restaurant_id = restaurant_ids[restaurant_name]  # Get the restaurant ID for the selected restaurant
        agent_id = random.choice(agent_ids)  # Randomly select a delivery agent

        # Status distribution
        status_roll = random.random()  # Generate a random number to determine the order status
        if status_roll < 0.75:  # 75% chance for 'DELIVERED'
            status = 'DELIVERED'
        elif status_roll < 0.88:  
            status = 'CANCELLED'
        elif status_roll < 0.95:
            status = 'IN_PROGRESS'
        else:
            status = 'PLACED'

        # Select 1 to 4 random items from the restaurant's menu
        available_items = item_ids[restaurant_name]  # Get the available items for the selected restaurant
        num_items = random.randint(1, 4)  # Randomly select the number of items to order
        selected = random.sample(available_items, min(num_items, len(available_items)))  # Randomly select the items from the available items

        # Calculate total amount
        total = 0
        order_items_data = []
        for item_id, base_price in selected:  # Loop through the selected items to calculate the total amount
            quantity = random.randint(1, 3)  # Randomly select the quantity for each item
            total += base_price * quantity  # Add the price of the item multiplied by its quantity to the total
            order_items_data.append((item_id, quantity, base_price))  # Store the item ID, quantity, and unit price for later insertion

        delivery_fee = random.choice([0, 20, 30, 40, 49])  # Randomly select a delivery fee
        total_with_fee = round(total + delivery_fee, 2)  # Calculate the total amount including the delivery fee

        created = random_date(90)  # Generate a random creation date for the order within the last 90 days

        # Delivered orders get a delivered_at timestamp
        
        delivered_at = None
        if status == 'DELIVERED':
            # Delivered at is after created_at, with a random delay of 25 to 75 minutes
            created_dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
            minutes = random.randint(25, 75)  # Random delay between 25 and 75 minutes
            delivered_dt = created_dt + timedelta(minutes=minutes)  # Calculate the delivered_at timestamp by adding the delay to the created_at timestamp
            delivered_at = delivered_dt.strftime("%Y-%m-%d %H:%M:%S")   # Format the delivered_at timestamp for SQLite

        # Cancelled orders have no agent assigned
        if status == 'CANCELLED':
            agent_id = None  # Set the agent_id to None for cancelled orders

        # Now, Insert the order into the orders table
        cursor.execute('''
            Insert INTO orders (customer_id, restaurant_id, agent_id, status, total_amount, delivery_fee, created_at, delivered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, restaurant_id, agent_id, status, total_with_fee, delivery_fee, created, delivered_at))
        order_id = cursor.lastrowid  # Get the last inserted order ID

        # Insert order items into the order_items table
        for item_id, quantity, unit_price in order_items_data:  # Loop through the order items data to insert them into the order_items table
            cursor.execute('''
                INSERT INTO order_items (order_id, item_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item_id, quantity, unit_price))  # Insert the order item into the order_items table

    conn.commit()  # Commit the changes to the database
    conn.close()  # Close the database connection

    print("Database created and seeded successfully!")  # Print a success message
    print(f"Database file Location: {DB_PATH}")  # Print the path to the database file

# Function to verify the database contents
def verify_database():
    conn = sqlite3.connect(DB_PATH)  # Connect to the SQLite database
    cursor = conn.cursor()  # Create a cursor object to execute SQL commands

    # Verify the number of records in each table
    tables = ["users", "restaurants", "menu_items", "orders", "order_items"]

    print("\nDatabase Verification:")
    print("-" * 40)
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")  # Execute a query to count the number of records in the current table
        count = cursor.fetchone()[0]  # Fetch the count result
        print(f"Table '{table}' has {count} rows.")  # Print the count of records(rows) for the current table

    print("\nSample delivered order:")
    cursor.execute('''
        SELECT o.order_id, u.name AS customer_name, r.name AS restaurant_name, o.status, o.total_amount
        FROM orders o
        JOIN users u ON o.customer_id = u.user_id
        JOIN restaurants r ON o.restaurant_id = r.restaurant_id
        WHERE o.status = 'DELIVERED'
        LIMIT 1
    ''')  # Execute a query to fetch a random delivered order along with customer and restaurant details
    row = cursor.fetchone()  # Fetch the result of the query
    if row:
        print(f"Order  #{row[0]} :  {row[1]} from " f"{row[2]} - {row[3]} ({row[4]})")  # Print the details of the fetched delivered order

    print("\nRevenue by cuisine type:")
    cursor.execute('''
        SELECT r.cuisine_type, COUNT(o.order_id) as orders, ROUND(SUM(o.total_amount), 2) AS total_revenue
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.restaurant_id
        WHERE o.status = 'DELIVERED'
        GROUP BY r.cuisine_type
        ORDER BY total_revenue DESC
    ''')  # Execute a query to calculate the total revenue by cuisine type for delivered orders
    for row in cursor.fetchall():   # Loop through the results of the query to print the revenue by cuisine type
        print(f"{row[0]}: {row[1]} orders, " f"₹{row[2]} revenue")  # Print the cuisine type and its corresponding total revenue
    conn.close()  # Close the database connection

if __name__ == "__main__":      # Check if the script is being run directly (not imported as a module)  
    create_database()  # Call the function to create and seed the database
    verify_database()  # Call the function to verify the database contents
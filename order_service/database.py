"""
database.py

This module initializes the orders or catalog database for the Order or Catalog Service of Bazar.com.
It creates the 'orders' or 'books' table if it doesn't exist, ensuring the database is ready for records.

The 'orders' table schema (for Order Service):
- order_id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique identifier for each order.
- item_id (INTEGER): The ID of the item purchased.
- quantity (INTEGER): The quantity of the item purchased.
- timestamp (TEXT): The date and time when the order was placed.

The 'books' table schema (for Catalog Service):
- id (INTEGER PRIMARY KEY): Unique identifier for each book.
- title (TEXT): The title of the book.
- topic (TEXT): The category or topic of the book.
- quantity (INTEGER): Number of copies available.
- price (REAL): The price of the book.

Environment Variables:
- DATABASE: Specifies the filename for the database (orders.db or catalog.db). Defaults to 'orders.db' if not set.
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def init_db(service_type='order'):
    """
    Initializes the database based on the service type (Order or Catalog Service).

    Parameters:
        service_type (str): Type of service ('order' or 'catalog') to determine table creation.
                            Defaults to 'order'.

    - Connects to the SQLite database specified in the DATABASE environment variable.
    - Creates the required table if it doesn't exist, based on the service type.
        - For Order Service, creates the 'orders' table.
        - For Catalog Service, creates the 'books' table.
    - Closes the database connection after setup.

    Logs:
        Confirmation message indicating successful database initialization, or an error if initialization fails.
    """
    database_path = os.environ.get('DATABASE', 'orders.db')
    conn = None
    try:

        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        if service_type == 'order':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    quantity INTEGER,
                    timestamp TEXT
                )
            ''')
            logging.info("Orders database initialized successfully.")
        elif service_type == 'catalog':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    topic TEXT,
                    quantity INTEGER,
                    price REAL
                )
            ''')
            logging.info("Catalog database initialized successfully.")
        else:
            logging.error(f"Invalid service type: {service_type}")
            return

        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {e}")
    finally:
        if conn:
            conn.close()

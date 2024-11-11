"""
database.py

This module initializes the orders database for the Order Service of Bazar.com.
It creates the 'orders' table if it doesn't exist, ensuring the database is ready for order records.

The 'orders' table schema:
- order_id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique identifier for each order.
- item_id (INTEGER): The ID of the item purchased.
- quantity (INTEGER): The quantity of the item purchased.
- timestamp (TEXT): The date and time when the order was placed.

Environment Variables:
- DATABASE: Specifies the filename for the orders database. Defaults to 'orders.db' if not set.
"""

import sqlite3
import os
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def init_db():
    """
    Initializes the orders database.

    - Connects to the SQLite database specified in the DATABASE environment variable.
    - Creates the 'orders' table if it doesn't exist with the following columns:
        - order_id: Auto-incrementing primary key.
        - item_id: ID of the purchased item.
        - quantity: Quantity purchased.
        - timestamp: Timestamp of the purchase.
    - Closes the database connection after setup.

    Logs:
        A confirmation message indicating that the orders database has been initialized.
    """
    database_path = os.environ.get('DATABASE', 'orders.db')
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                quantity INTEGER,
                timestamp TEXT
            )
        ''')
        conn.commit()
        logging.info("Orders database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {e}")
    finally:
        conn.close()

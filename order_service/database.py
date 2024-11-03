import sqlite3

# order_service/database.py

import sqlite3
import os

def init_db():
    # Get the database filename from environment variables or default to 'orders.db'
    DATABASE = os.environ.get('DATABASE', 'orders.db')
    
    conn = sqlite3.connect(DATABASE)
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
    conn.close()
    print("Orders database initialized.")


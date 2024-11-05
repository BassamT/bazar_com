"""
database.py

This module provides a function to initialize the catalog database for Bazar.com.
It creates the 'books' table if it doesn't exist and seeds it with initial data.
"""

import sqlite3

def init_db():
    """
    Initializes the catalog database.

    - Connects to the 'catalog.db' SQLite database.
    - Creates the 'books' table if it doesn't exist.
    - Seeds initial data into the 'books' table if it's empty.

    The 'books' table has the following schema:
        - id (INTEGER PRIMARY KEY): Unique identifier for each book.
        - title (TEXT): The title of the book.
        - topic (TEXT): The topic or category of the book.
        - quantity (INTEGER): The number of copies available.
        - price (REAL): The price of the book.

    Initial data seeded includes four books with predefined details.
    """
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT,
            topic TEXT,
            quantity INTEGER,
            price REAL
        )
    ''')
    # Seed initial data if table is empty
    cursor.execute('SELECT COUNT(*) FROM books')
    if cursor.fetchone()[0] == 0:
        books = [
            (1, 'How to get a good grade in DOS in 40 minutes a day', 'distributed systems', 10, 50.0),
            (2, 'RPCs for Noobs', 'distributed systems', 10, 25.0),
            (3, 'Xen and the Art of Surviving Undergraduate School', 'undergraduate school', 10, 75.0),
            (4, 'Cooking for the Impatient Undergrad', 'undergraduate school', 10, 100.0),
        ]
        cursor.executemany('INSERT INTO books VALUES (?, ?, ?, ?, ?)', books)
        conn.commit()
        print("Database initialized with default books.")
    conn.close()

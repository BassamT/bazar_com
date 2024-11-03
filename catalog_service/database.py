# catalog_service/database.py

import sqlite3
import os

def init_db():
    # Get the database filename from environment variables or default to 'catalog.db'
    DATABASE = os.environ.get('DATABASE', 'catalog.db')
    
    conn = sqlite3.connect(DATABASE)
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
            # Existing books
            (1, 'How to get a good grade in DOS in 40 minutes a day', 'distributed systems', 10, 50.0),
            (2, 'RPCs for Noobs', 'distributed systems', 10, 25.0),
            (3, 'Xen and the Art of Surviving Undergraduate School', 'undergraduate school', 10, 75.0),
            (4, 'Cooking for the Impatient Undergrad', 'undergraduate school', 10, 100.0),
            # New books added
            (5, 'How to finish Project 3 on time', 'project management', 10, 60.0),
            (6, 'Why theory classes are so hard', 'education', 10, 40.0),
            (7, 'Spring in the Pioneer Valley', 'travel', 10, 30.0),
        ]
        cursor.executemany('INSERT INTO books VALUES (?, ?, ?, ?, ?)', books)
        conn.commit()
        print("Database initialized with default books.")
    conn.close()

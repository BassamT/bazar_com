import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def init_db():
    """
    Initializes the catalog database.
    
    - Retrieves the database path from an environment variable.
    - Creates the 'books' table if it doesn't exist.
    - Seeds initial data, including newly added books, if the table is empty.
    """
    DATABASE = os.environ.get('DATABASE', 'catalog.db')

    try:
        with sqlite3.connect(DATABASE) as conn:
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
            cursor.execute('SELECT COUNT(*) FROM books')
            if cursor.fetchone()[0] == 0:
                books = [
                    (1, 'How to get a good grade in DOS in 40 minutes a day', 'distributed systems', 10, 50.0),
                    (2, 'RPCs for Noobs', 'distributed systems', 10, 25.0),
                    (3, 'Xen and the Art of Surviving Undergraduate School', 'undergraduate school', 10, 75.0),
                    (4, 'Cooking for the Impatient Undergrad', 'undergraduate school', 10, 100.0),
                    (5, 'How to finish Project 3 on time', 'project management', 10, 60.0),
                    (6, 'Why theory classes are so hard', 'education', 10, 40.0),
                    (7, 'Spring in the Pioneer Valley', 'travel', 10, 30.0),
                ]
                cursor.executemany('INSERT INTO books VALUES (?, ?, ?, ?, ?)', books)
                conn.commit()
                logging.info("Database initialized with default books.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")


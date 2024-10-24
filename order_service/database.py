import sqlite3

def init_db():
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
    conn.close()

"""
catalog_service.py

This module implements the Catalog Service for Bazar.com, an online bookstore.
It handles search, info, and update operations on the book catalog.
It also includes a background thread that periodically restocks items.
"""

from flask import Flask, jsonify, request
import sqlite3
from database import init_db
import threading
import time
import logging

app = Flask(__name__)
DATABASE = 'catalog.db'

# Create a lock object to ensure thread safety during database operations
db_lock = threading.Lock()

def restock_items():
    """
    Background thread function that periodically increases the quantity of each book.

    This function runs in an infinite loop, sleeping for a specified interval (default is 60 seconds),
    and then increments the quantity of all books in the catalog by 5.
    It uses a threading lock to ensure thread safety during database operations.
    """
    while True:
        time.sleep(60)  # Restock every 60 seconds
        with db_lock:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                # Increase the quantity of each book by 5
                cursor.execute('UPDATE books SET quantity = quantity + 5')
                conn.commit()
                conn.close()
                logging.info("Stock updated: Each item's quantity increased by 5.")
            except Exception as e:
                logging.info(f"Error in restocking items: {e}")

@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    """
    Handles GET requests to /search/<topic>.

    Queries the catalog database for books matching the given topic and returns a list of books.

    Parameters:
        topic (str): The topic to search for.

    Returns:
        Response: A JSON response containing a list of books with their IDs and titles.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM books WHERE topic=?', (topic,))
    books = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(books)

@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    """
    Handles GET requests to /info/<item_id>.

    Retrieves detailed information about a book, including its title, quantity, and price.

    Parameters:
        item_id (int): The ID of the book to retrieve information for.

    Returns:
        Response: A JSON response containing the book's details,
                  or an error message with a 404 status code if not found.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT title, quantity, price FROM books WHERE id=?', (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({'title': row[0], 'quantity': row[1], 'price': row[2]})
    else:
        return jsonify({'error': 'Item not found'}), 404

@app.route('/update/<int:item_id>', methods=['PUT'])
def update(item_id):
    """
    Handles PUT requests to /update/<item_id>.

    Updates the quantity and/or price of a book specified by its ID.

    Expects a JSON payload with 'quantity' and/or 'price' fields.

    Parameters:
        item_id (int): The ID of the book to update.

    Returns:
        Response: A JSON response indicating the result of the operation.
    """
    data = request.get_json()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    if 'quantity' in data:
        cursor.execute('UPDATE books SET quantity=? WHERE id=?', (data['quantity'], item_id))
    if 'price' in data:
        cursor.execute('UPDATE books SET price=? WHERE id=?', (data['price'], item_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Item updated'})

if __name__ == '__main__':
    init_db()
    # Start the restocking thread
    threading.Thread(target=restock_items, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, debug=True)

"""
catalog_service.py

This module implements the Catalog Service for Bazar.com, an online bookstore.
It handles search, info, and update operations on the book catalog.
It also includes a background thread that periodically restocks items.
It now supports replication synchronization, cache invalidation, and enhanced error handling.
"""

from flask import Flask, jsonify, request
from database import init_db
import sqlite3
import threading
import time
import requests
import logging
import os

app = Flask(__name__)

# Configuration from environment variables
DATABASE = os.environ.get('DATABASE', 'catalog.db')
PORT = int(os.environ.get('PORT', 5001))
CURRENT_REPLICA_URL = os.environ.get('CURRENT_REPLICA_URL', f'http://localhost:{PORT}')
REPLICA_URLS = os.environ.get('REPLICA_URLS', '').split(',')
FRONTEND_CACHE_INVALIDATE_URL = os.environ.get('FRONTEND_CACHE_INVALIDATE_URL', 'http://frontend_service:5000/invalidate')

# Thread lock for thread safety
db_lock = threading.Lock()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def restock_items():
    """
    Background thread function that periodically increases the quantity of each book.
    """
    while True:
        time.sleep(60)  # Restock every 60 seconds
        with db_lock:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('UPDATE books SET quantity = quantity + 5')
                conn.commit()
                # Get all item IDs
                cursor.execute('SELECT id FROM books')
                item_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
                logging.info("Stock updated: Each item's quantity increased by 5.")
                
                # Invalidate cache for all items
                for item_id in item_ids:
                    send_cache_invalidate(item_id)
                
                # Propagate restock to other replicas
                data = {'restock': True}
                propagate_update(data)
            except Exception as e:
                logging.error(f"Error in restocking items: {e}")


def send_cache_invalidate(item_id):
    """
    Sends a cache invalidation request to the Front-End Service.

    Parameters:
        item_id (int): ID of the item to invalidate in cache.
    """
    try:
        response = requests.post(f"{FRONTEND_CACHE_INVALIDATE_URL}/{item_id}")
        if response.status_code == 200:
            logging.info(f"Cache invalidated for item_id: {item_id}")
        else:
            logging.error(f"Failed to invalidate cache for item_id: {item_id}")
    except Exception as e:
        logging.error(f"Error sending cache invalidate request: {e}")


def propagate_update(data):
    """
    Propagates updates to other replicas to maintain consistency.

    Parameters:
        data (dict): Data to send to replicas, which includes item ID and updated values.
    """
    for url in REPLICA_URLS:
        if url != CURRENT_REPLICA_URL and url:
            try:
                response = requests.post(f"{url}/replica_update", json=data)
                if response.status_code == 200:
                    logging.info(f"Update propagated to {url}")
                else:
                    logging.error(f"Failed to propagate update to {url}")
            except Exception as e:
                logging.error(f"Error propagating update to {url}: {e}")


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
    logging.info(f"Received search request for topic: {topic}")
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, title FROM books WHERE topic=?', (topic,))
        books = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify(books)
    except Exception as e:
        logging.error(f"Error in search: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    """
    Handles GET requests to /info/<item_id>.
    Retrieves detailed information about a book, including its title, quantity, and price.
    
    Parameters:
        item_id (int): The ID of the book to retrieve information for.
    
    Returns:
        Response: A JSON response containing the book's details, or a 404 error if not found.
    """
    logging.info(f"Received info request for item_id: {item_id}")
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT title, quantity, price FROM books WHERE id=?', (item_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify({'title': row[0], 'quantity': row[1], 'price': row[2]})
        else:
            logging.warning(f"Item not found: {item_id}")
            return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logging.error(f"Error in info: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


@app.route('/update/<int:item_id>', methods=['PUT'])
def update(item_id):
    """
    Handles PUT requests to /update/<item_id>.
    Updates the quantity and/or price of a book specified by its ID.
    
    Parameters:
        item_id (int): The ID of the book to update.
    
    Returns:
        Response: A JSON response indicating the result of the operation.
    """
    data = request.get_json()
    if not data:
        logging.warning("No data provided in update request.")
        return jsonify({'error': 'No data provided.'}), 400

    quantity = data.get('quantity')
    price = data.get('price')

    if quantity is not None and not isinstance(quantity, int):
        logging.warning("Invalid quantity type provided.")
        return jsonify({'error': 'Quantity must be an integer.'}), 400

    if price is not None and not isinstance(price, (int, float)):
        logging.warning("Invalid price type provided.")
        return jsonify({'error': 'Price must be a number.'}), 400

    # Invalidate cache before updating
    send_cache_invalidate(item_id)

    with db_lock:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            if quantity is not None:
                cursor.execute('UPDATE books SET quantity=? WHERE id=?', (quantity, item_id))
            if price is not None:
                cursor.execute('UPDATE books SET price=? WHERE id=?', (price, item_id))
            conn.commit()
            conn.close()
            logging.info(f"Updated item_id: {item_id} with data: {data}")

            # Propagate update to other replicas
            data_to_propagate = {'item_id': item_id, 'quantity': quantity, 'price': price}
            propagate_update(data_to_propagate)

            return jsonify({'message': 'Item updated'})
        except Exception as e:
            logging.error(f"Error in update: {e}")
            return jsonify({'error': 'An error occurred while updating the item.'}), 500


@app.route('/replica_update', methods=['POST'])
def replica_update():
    """
    Endpoint to receive updates from other replicas.
    Synchronizes the local database with changes made in other replicas.
    
    Returns:
        Response: A JSON message indicating the success of the operation.
    """
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    price = data.get('price')

    if not item_id:
        return jsonify({'error': 'No item_id provided.'}), 400

    with db_lock:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            if quantity is not None:
                cursor.execute('UPDATE books SET quantity=? WHERE id=?', (quantity, item_id))
            if price is not None:
                cursor.execute('UPDATE books SET price=? WHERE id=?', (price, item_id))
            conn.commit()
            conn.close()
            logging.info(f"Replica updated item_id: {item_id} with data: {data}")
            return jsonify({'message': 'Replica updated'})
        except Exception as e:
            logging.error(f"Error in replica update: {e}")
            return jsonify({'error': 'An error occurred while updating the replica.'}), 500


if __name__ == '__main__':
    init_db()
    threading.Thread(target=restock_items, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)

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

DATABASE = os.environ.get('DATABASE', 'catalog.db')
PORT = int(os.environ.get('PORT', 5001))
CURRENT_REPLICA_URL = os.environ.get('CURRENT_REPLICA_URL', f'http://localhost:{PORT}')
REPLICA_URLS = os.environ.get('REPLICA_URLS', '').split(',')
FRONTEND_CACHE_INVALIDATE_URL = os.environ.get('FRONTEND_CACHE_INVALIDATE_URL', 'http://frontend_service:5000/invalidate')

db_lock = threading.Lock()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def restock_items():
    """
    Background thread function that periodically increases the quantity of each book.
    This function includes improved error handling, optimized cache invalidation, and a delay mechanism.
    """
    while True:
<<<<<<< HEAD
        time.sleep(30)  # Restock every 60 seconds 
=======
        time.sleep(60)  # Restock every 60 seconds 
>>>>>>> a439d0be3c29efed99907a0c8cfa5895b3895406
        with db_lock:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()

                # Increment quantity for each book
                restock_amount = 5
                cursor.execute('UPDATE books SET quantity = quantity + ?', (restock_amount,))
                conn.commit()

                # Retrieve all item IDs for cache invalidation
                cursor.execute('SELECT id FROM books')
                item_ids = [row[0] for row in cursor.fetchall()]
                logging.info("Stock updated: Each item's quantity increased by 5.")
            except sqlite3.Error as e:
                logging.error(f"Database error during restock operation: {e}")
            except Exception as e:
                logging.error(f"Unexpected error in restocking items: {e}")
            finally:
                if conn:
                    conn.close()

        for item_id in item_ids:
            send_cache_invalidate(item_id)

        # Propagate restock update to replicas
        data = {'restock': True}
        propagate_update(data)




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
    Propagates updates to other catalog service replicas to maintain consistency.

    Parameters:
        data (dict): The data to propagate. This can include:
            - 'item_id' (int): The ID of the item that was updated.
            - 'quantity' (int, optional): The new quantity of the item.
            - 'price' (float, optional): The new price of the item.
            - 'restock' (bool, optional): A flag indicating if this is a restock operation.

    Behavior:
        - Sends a POST request with the provided data to the '/replica_update' endpoint
          of each replica in the REPLICA_URLS list.
        - Skips sending the update to itself by checking CURRENT_REPLICA_URL.
        - Does not propagate updates received from other replicas to prevent update loops.
    """
    logging.info(f"Starting propagation of update with data: {data}")
    for url in REPLICA_URLS:
        # Skip if the URL is empty or if it's the current replica
        if not url or url == CURRENT_REPLICA_URL:
            continue
        try:
            response = requests.post(f"{url}/replica_update", json=data)
            if response.status_code == 200:
                logging.info(f"Successfully propagated update to {url}: {data}")
            else:
                logging.error(f"Failed to propagate update to {url}. Status code: {response.status_code}, "
                              f"Response: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error when trying to propagate update to {url}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during propagation to {url}: {e}")
    # Do NOT propagate updates received from other replicas to prevent loops


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
            logging.info(f"Updated item_id: {item_id} with data: {data}")
        except Exception as e:
            logging.error(f"Error in update: {e}")
            return jsonify({'error': 'An error occurred while updating the item.'}), 500
        finally:
            if conn:
                conn.close()

    # Propagate update to other replicas after releasing lock
    data_to_propagate = {'item_id': item_id, 'quantity': quantity, 'price': price}
    propagate_update(data_to_propagate)

    return jsonify({'message': 'Item updated'})



@app.route('/replica_update', methods=['POST'])
def replica_update():
    """
    Endpoint to receive updates from other replicas for synchronization.

    Expects:
        - A JSON payload containing update data:
            - For restock operations:
                - 'restock' (bool): Should be True.
            - For item updates:
                - 'item_id' (int): The ID of the item to update.
                - 'quantity' (int, optional): The new quantity for the item.
                - 'price' (float, optional): The new price for the item.

    Behavior:
        - If a restock operation is received, it increases the quantity of all items by a fixed amount.
        - For item-specific updates, it updates the specified fields in the local database.
        - Does NOT propagate the update further to avoid update loops.
        - Does NOT run restock operations independently; only applies restock updates received from the primary.

    Returns:
        - A JSON response indicating success or failure with appropriate HTTP status codes.
    """
    data = request.get_json()
    logging.info(f"Received data for catalog replica update: {data}")

    # Check if this is a restock request
    if data.get('restock') == True:
        with db_lock:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                # Increase quantity of every item by the restock amount
                restock_amount = 5
                cursor.execute('UPDATE books SET quantity = quantity + ?', (restock_amount,))
                conn.commit()
                conn.close()
                logging.info("Restock applied to all items in the database.")
                return jsonify({'message': 'Restock applied to all items'}), 200
            except sqlite3.Error as e:
                logging.error(f"Error in restock operation: {e}")
                return jsonify({'error': 'An error occurred during restock.'}), 500
        
        # Restock updates are only propagated by the primary replica
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    price = data.get('price')

    if not item_id:
        logging.error("replica_update missing item_id")
        return jsonify({'error': 'No item_id provided.'}), 400

    if quantity is None and price is None:
        logging.error("replica_update missing both quantity and price")
        return jsonify({'error': 'No quantity or price provided for update.'}), 400

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
            return jsonify({'message': 'Replica updated'}), 200
        except sqlite3.Error as e:
            logging.error(f"Error in replica update: {e}")
            return jsonify({'error': 'An error occurred while updating the replica.'}), 500
        except Exception as e:
            logging.error(f"Unexpected error during replica update: {e}")
            return jsonify({'error': 'An unexpected error occurred.'}), 500
    # Do NOT propagate updates received from other replicas



if __name__ == '__main__':
    init_db()
    # Only run restock_items if this instance is the primary
    if os.environ.get('IS_PRIMARY', 'false').lower() == 'true':
        threading.Thread(target=restock_items, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)

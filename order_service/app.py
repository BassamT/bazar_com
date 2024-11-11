"""
order_service.py

This module implements the Order Service for Bazar.com, an online bookstore.
It processes purchase requests by interacting with the Catalog Service to check stock,
updates inventory, and records orders in the local database. It also supports replication,
cache invalidation, and load balancing across multiple catalog service instances.

Endpoints provided by this service:
- /purchase/<item_id>      : Purchase a book by its ID.
- /orders                  : Retrieve all orders placed.
- /replica_purchase        : Receive purchase updates from other replicas to maintain consistency.
"""

from flask import Flask, jsonify, request
from database import init_db

import requests
import sqlite3
import threading
import logging
import datetime
import os

app = Flask(__name__)

# Configuration from environment variables
DATABASE = os.environ.get('DATABASE', 'orders.db')
PORT = int(os.environ.get('PORT', 5002))
CURRENT_REPLICA_URL = os.environ.get('CURRENT_REPLICA_URL', f'http://localhost:{PORT}')
REPLICA_URLS = os.environ.get('REPLICA_URLS', '').split(',')
CATALOG_SERVICE_URLS = os.environ.get('CATALOG_SERVICE_URLS', '').split(',')
FRONTEND_CACHE_INVALIDATE_URL = os.environ.get('FRONTEND_CACHE_INVALIDATE_URL', 'http://frontend_service:5000/invalidate')

# Thread lock for thread safety
db_lock = threading.Lock()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Load balancing index for Catalog Service
catalog_index = 0

def get_catalog_service_url():
    """
    Retrieves the URL for the next catalog service in a round-robin fashion.

    Returns:
        str: URL of the selected catalog service, or None if no URLs are configured.
    """
    global catalog_index
    if not CATALOG_SERVICE_URLS or CATALOG_SERVICE_URLS == ['']:
        logging.error("No Catalog Service URLs configured.")
        return None
    url = CATALOG_SERVICE_URLS[catalog_index]
    catalog_index = (catalog_index + 1) % len(CATALOG_SERVICE_URLS)
    return url

def propagate_update(data):
    """
    Propagates purchase updates to other replicas to maintain data consistency.

    Parameters:
        data (dict): Purchase data to propagate, including item_id, quantity, and timestamp.
    """
    for url in REPLICA_URLS:
        if url != CURRENT_REPLICA_URL and url:
            try:
                response = requests.post(f"{url}/replica_purchase", json=data, timeout=5)
                if response.status_code == 200:
                    logging.info(f"Purchase propagated to {url}")
                else:
                    logging.error(f"Failed to propagate purchase to {url}")
            except Exception as e:
                logging.error(f"Error propagating purchase to {url}: {e}")

def send_cache_invalidate(item_id):
    """
    Sends a cache invalidation request to the Front-End Service.

    Parameters:
        item_id (int): ID of the item to invalidate in the cache.
    """
    try:
        response = requests.post(f"{FRONTEND_CACHE_INVALIDATE_URL}/{item_id}", timeout=5)
        if response.status_code == 200:
            logging.info(f"Cache invalidated for item_id: {item_id}")
        else:
            logging.error(f"Failed to invalidate cache for item_id: {item_id}")
    except Exception as e:
        logging.error(f"Error sending cache invalidate request: {e}")

@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
    """
    Handles PUT requests to /purchase/<item_id>.
    Processes a purchase request by checking stock, updating inventory, and recording the order.

    Parameters:
        item_id (int): The ID of the book to purchase.

    Returns:
        Response: A JSON response indicating the result of the purchase operation.
    """
    logging.info(f"Received purchase request for item_id: {item_id}")
    try:
        # Validate item_id
        if item_id <= 0:
            logging.warning(f"Invalid item_id: {item_id}")
            return jsonify({'error': 'Invalid item ID'}), 400

        # Get a Catalog Service URL (using round-robin load balancing)
        catalog_url = get_catalog_service_url()
        if not catalog_url:
            return jsonify({'error': 'No Catalog Service available'}), 503

        # Check item info from Catalog Service
        response = requests.get(f"{catalog_url}/info/{item_id}", timeout=5)
        if response.status_code != 200:
            logging.error(f"Item not found: {item_id}")
            return jsonify({'error': 'Item not found'}), 404
        item_info = response.json()
        if item_info['quantity'] <= 0:
            logging.info(f"Item out of stock: {item_id}")
            return jsonify({'error': 'Item out of stock'}), 400

        # Decrement quantity in Catalog Service
        new_quantity = item_info['quantity'] - 1
        logging.info(f"Updating item_id: {item_id} with new quantity: {new_quantity}")

        # Invalidate cache before updating
        send_cache_invalidate(item_id)

        # Update Catalog Service
        update_response = requests.put(f"{catalog_url}/update/{item_id}", json={'quantity': new_quantity}, timeout=5)
        if update_response.status_code != 200:
            logging.error(f"Failed to update stock for item_id: {item_id}. Response: {update_response.text}")
            return jsonify({'error': 'Failed to update stock'}), 500

        # Record the order
        with db_lock:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                timestamp = datetime.datetime.now().isoformat()
                cursor.execute('INSERT INTO orders (item_id, quantity, timestamp) VALUES (?, ?, ?)', (item_id, 1, timestamp))
                conn.commit()
                conn.close()
                logging.info(f"Order recorded for item_id: {item_id}")
            except sqlite3.Error as e:
                logging.error(f"Error recording order: {e}")
                return jsonify({'error': 'Failed to record order'}), 500

        # Propagate purchase to other replicas
        data_to_propagate = {'item_id': item_id, 'quantity': 1, 'timestamp': timestamp}
        propagate_update(data_to_propagate)

        # Log purchase with book title
        book_title = item_info.get('title', 'Unknown Title')
        logging.info(f"Bought book '{book_title}'")
        return jsonify({'message': f'Purchased item {item_id}'})
    except Exception as e:
        logging.error(f"Error in purchase: {e}")
        return jsonify({'error': 'An error occurred while processing your purchase.'}), 500

@app.route('/replica_purchase', methods=['POST'])
def replica_purchase():
    """
    Endpoint to receive purchase updates from other replicas.

    This endpoint ensures consistency across replicas by recording purchase transactions from other instances.

    Returns:
        Response: JSON message indicating success or failure of the replication.
    """
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    timestamp = data.get('timestamp')

    if not item_id or not quantity or not timestamp:
        logging.warning("Incomplete data received for replica purchase")
        return jsonify({'error': 'Incomplete data provided.'}), 400

    with db_lock:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO orders (item_id, quantity, timestamp) VALUES (?, ?, ?)', (item_id, quantity, timestamp))
            conn.commit()
            conn.close()
            logging.info(f"Replica recorded purchase for item_id: {item_id}")
            return jsonify({'message': 'Replica purchase recorded'}), 200
        except sqlite3.Error as e:
            logging.error(f"Error in replica purchase: {e}")
            return jsonify({'error': 'An error occurred while recording the purchase.'}), 500

@app.route('/orders', methods=['GET'])
def get_all_orders():
    """
    Handles GET requests to /orders.
    Retrieves all orders from the orders database.

    Returns:
        Response: A JSON response containing a list of all orders or an error message.
    """
    logging.info("Retrieving all orders")
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders')
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        # Convert rows to list of dictionaries
        orders = [dict(zip(column_names, row)) for row in rows]
        return jsonify(orders), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({'error': f'Database error: {e}'}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=PORT)

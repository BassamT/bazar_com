"""
order_service.py

This module implements the Order Service for Bazar.com, an online bookstore.
It handles purchase requests by interacting with the Catalog Service to check stock,
updates inventory, and records orders in the database.

Endpoints provided by this service:
- /purchase/<item_id> : Purchase a book by its ID.
- /orders             : Retrieve all orders placed.
"""

from flask import Flask, jsonify, request
import requests
import sqlite3
from database import init_db
import datetime

app = Flask(__name__)
DATABASE = 'orders.db'
CATALOG_SERVICE_URL = 'http://catalog_service:5001'

@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
    """
    Handles PUT requests to /purchase/<item_id>.

    Processes a purchase of a book by its ID. It performs the following steps:
    - Checks the item's availability by querying the Catalog Service.
    - Decrements the item's quantity in the Catalog Service if in stock.
    - Records the order in the local orders database.

    Parameters:
        item_id (int): The ID of the book to purchase.

    Returns:
        Response: A JSON response indicating the result of the purchase operation,
                  or an error message with an appropriate HTTP status code.
    """
    # Check item info from Catalog Service
    response = requests.get(f"{CATALOG_SERVICE_URL}/info/{item_id}")
    if response.status_code != 200:
        return jsonify({'error': 'Item not found'}), 404
    item_info = response.json()
    if item_info['quantity'] <= 0:
        return jsonify({'error': 'Item out of stock'}), 400
    # Decrement quantity in Catalog Service
    new_quantity = item_info['quantity'] - 1
    update_response = requests.put(f"{CATALOG_SERVICE_URL}/update/{item_id}", json={'quantity': new_quantity})
    if update_response.status_code != 200:
        return jsonify({'error': 'Failed to update stock'}), 500
    # Record the order
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Get current timestamp
    current_timestamp = datetime.datetime.now().isoformat()

    # Insert the order with timestamp
    cursor.execute(
        'INSERT INTO orders (item_id, quantity, timestamp) VALUES (?, ?, ?)',
        (item_id, 1, current_timestamp)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': f'Purchased item {item_id}'})

@app.route('/orders', methods=['GET'])
def get_all_orders():
    """
    Handles GET requests to /orders.

    Retrieves all orders from the orders database and returns them as a JSON response.

    Returns:
        Response: A JSON response containing a list of all orders,
                  or an error message with a 500 status code in case of a database error.
    """
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders')
        rows = cursor.fetchall()
        # Get column names from the cursor description
        column_names = [description[0] for description in cursor.description]
        conn.close()

        # Convert rows to list of dictionaries
        orders = [dict(zip(column_names, row)) for row in rows]

        return jsonify(orders), 200
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {e}'}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=True)

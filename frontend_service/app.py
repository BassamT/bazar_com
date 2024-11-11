"""
frontend_service.py

This module implements the Frontend Service for Bazar.com, an online bookstore.
It acts as an API Gateway that proxies client requests to the appropriate backend services:
- Catalog Service: Handles book catalog operations.
- Order Service: Handles purchase and order retrieval operations.

Endpoints provided by this service:
- /search/<topic>     : Search for books by topic.
- /info/<item_id>     : Get detailed information about a specific book.
- /purchase/<item_id> : Purchase a book by its ID.
- /orders             : Retrieve all orders placed.
"""
#noor
from flask import Flask, jsonify
import requests

app = Flask(__name__)

CATALOG_SERVICE_URL = 'http://catalog_service:5001'
ORDER_SERVICE_URL = 'http://order_service:5002'

@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    """
    Handles GET requests to /search/<topic>.

    Forwards the search request to the Catalog Service to find books matching the given topic.

    Parameters:
        topic (str): The topic to search for.

    Returns:
        Response: A JSON response containing a list of books matching the topic.
    """
    response = requests.get(f"{CATALOG_SERVICE_URL}/search/{topic}")
    return jsonify(response.json())

@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    """
    Handles GET requests to /info/<item_id>.

    Retrieves detailed information about a specific book by forwarding the request to the Catalog Service.

    Parameters:
        item_id (int): The ID of the book to retrieve information for.

    Returns:
        Response: A JSON response containing the book's details.
    """
    response = requests.get(f"{CATALOG_SERVICE_URL}/info/{item_id}")
    return jsonify(response.json())

@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
    """
    Handles PUT requests to /purchase/<item_id>.

    Initiates the purchase of a book by forwarding the request to the Order Service.

    Parameters:
        item_id (int): The ID of the book to purchase.

    Returns:
        Response: A JSON response indicating the result of the purchase operation.
    """
    response = requests.put(f"{ORDER_SERVICE_URL}/purchase/{item_id}")
    return jsonify(response.json())

@app.route('/orders', methods=['GET'])
def get_all_orders():
    """
    Handles GET requests to /orders.

    Retrieves all orders by forwarding the request to the Order Service.

    Returns:
        Response: A JSON response containing a list of all orders and the corresponding status code.
    """
    response = requests.get(f"{ORDER_SERVICE_URL}/orders")
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

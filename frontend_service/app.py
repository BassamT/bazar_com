"""
frontend_service.py

This module implements the Frontend Service for Bazar.com, an online bookstore.
It acts as an API Gateway that proxies client requests to the appropriate backend services:
- Catalog Service: Handles book catalog operations.
- Order Service: Handles purchase and order retrieval operations.

The service includes load balancing, caching, and cache invalidation features to optimize performance.
Caching uses an LRU eviction policy to manage limited memory.

Endpoints provided by this service:
- /search/<topic>     : Search for books by topic (with caching).
- /info/<item_id>     : Get detailed information about a specific book (with caching).
- /purchase/<item_id> : Purchase a book by its ID (triggers cache invalidation).
- /invalidate/<item_id> : Invalidate cache entries for a specific book (used by backend services).
"""

from flask import Flask, jsonify, request
import requests
import logging
from collections import OrderedDict
import os

app = Flask(__name__)

CATALOG_SERVICE_URLS = os.environ.get('CATALOG_SERVICE_URLS', '').split(',')
ORDER_SERVICE_URLS = os.environ.get('ORDER_SERVICE_URLS', '').split(',')
CACHE_SIZE = int(os.environ.get('CACHE_SIZE', 100))

# Load balancing indices for round-robin
catalog_index = 0
order_index = 0

# In-memory cache using OrderedDict for LRU eviction
cache = OrderedDict()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def get_catalog_service_url():
    """
    Retrieves the URL for the next catalog service in round-robin fashion.

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


def get_order_service_url():
    """
    Retrieves the URL for the next order service in round-robin fashion.

    Returns:
        str: URL of the selected order service, or None if no URLs are configured.
    """
    global order_index
    if not ORDER_SERVICE_URLS or ORDER_SERVICE_URLS == ['']:
        logging.error("No Order Service URLs configured.")
        return None
    url = ORDER_SERVICE_URLS[order_index]
    order_index = (order_index + 1) % len(ORDER_SERVICE_URLS)
    return url


@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    """
    Handles GET requests to /search/<topic>.
    Searches for books by topic. Attempts to serve from cache first.

    Parameters:
        topic (str): The topic to search for.

    Returns:
        Response: JSON response containing a list of books matching the topic.
    """
    logging.info(f"Received search request for topic: {topic}")
    cache_key = f"search:{topic}"
    if cache_key in cache:
        logging.debug("Cache hit for search")
        cache.move_to_end(cache_key)
        return jsonify(cache[cache_key])
    
    logging.info("Cache miss for search")
    url = get_catalog_service_url()
    if not url:
        return jsonify({'error': 'No Catalog Service available'}), 503
    try:
        response = requests.get(f"{url}/search/{topic}", timeout=5)
        response.raise_for_status()
        data = response.json()
        # Add result to cache
        cache[cache_key] = data
        if len(cache) > CACHE_SIZE:
            cache.popitem(last=False)  # Evict the least recently used item
        return jsonify(data)
    except requests.RequestException as e:
        logging.error(f"Error in search: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    """
    Handles GET requests to /info/<item_id>.
    Retrieves detailed information about a specific book. Attempts to serve from cache first.

    Parameters:
        item_id (int): The ID of the book to retrieve information for.

    Returns:
        Response: JSON response containing the book's details.
    """
    logging.info(f"Received info request for item_id: {item_id}")
    cache_key = f"info:{item_id}"
    if cache_key in cache:
        logging.debug("Cache hit for info")
        cache.move_to_end(cache_key)
        return jsonify(cache[cache_key])
    
    logging.info("Cache miss for info")
    url = get_catalog_service_url()
    if not url:
        return jsonify({'error': 'No Catalog Service available'}), 503
    try:
        response = requests.get(f"{url}/info/{item_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
        # Add result to cache
        cache[cache_key] = data
        if len(cache) > CACHE_SIZE:
            cache.popitem(last=False)  # Evict the least recently used item
        return jsonify(data)
    except requests.RequestException as e:
        logging.error(f"Error in info: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
    """
    Handles PUT requests to /purchase/<item_id>.
    Initiates the purchase of a book, invalidates cache entries for the item, and forwards request to Order Service.

    Parameters:
        item_id (int): The ID of the book to purchase.

    Returns:
        Response: JSON response indicating the result of the purchase operation.
    """
    logging.info(f"Received purchase request for item_id: {item_id}")
    url = get_order_service_url()
    if not url:
        return jsonify({'error': 'No Order Service available'}), 503
    try:
        response = requests.put(f"{url}/purchase/{item_id}", timeout=5)
        response.raise_for_status()
        # Invalidate cache entries related to the item
        cache_key = f"info:{item_id}"
        if cache_key in cache:
            del cache[cache_key]
            logging.info(f"Cache invalidated for item_id: {item_id}")
        return jsonify(response.json())
    except requests.RequestException as e:
        logging.error(f"Error in purchase: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


@app.route('/invalidate/<int:item_id>', methods=['POST'])
def invalidate(item_id):
    """
    Endpoint to receive cache invalidation requests from backend services.

    Parameters:
        item_id (int): The ID of the book for which cache should be invalidated.

    Returns:
        Response: JSON message indicating cache invalidation success.
    """
    logging.info(f"Received cache invalidate request for item_id: {item_id}")
    # Invalidate specific item info cache
    cache_key_info = f"info:{item_id}"
    if cache_key_info in cache:
        del cache[cache_key_info]
        logging.info(f"Cache invalidated for key: {cache_key_info}")
    # Invalidate search caches that may include the item
    keys_to_delete = [key for key in cache if key.startswith('search:')]
    for key in keys_to_delete:
        del cache[key]
        logging.debug(f"Cache invalidated for key: {key}")
    return jsonify({'message': 'Cache invalidated'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

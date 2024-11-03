# frontend_service/app.py

from flask import Flask, jsonify, request
import requests
import logging
from collections import OrderedDict
import os

app = Flask(__name__)

# Configuration from environment variables
CATALOG_SERVICE_URLS = os.environ.get('CATALOG_SERVICE_URLS', '').split(',')
ORDER_SERVICE_URLS = os.environ.get('ORDER_SERVICE_URLS', '').split(',')
CACHE_SIZE = int(os.environ.get('CACHE_SIZE', 100))

# Load balancing indices
catalog_index = 0
order_index = 0

# In-memory cache using OrderedDict for LRU
cache = OrderedDict()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def get_catalog_service_url():
    global catalog_index
    if not CATALOG_SERVICE_URLS or CATALOG_SERVICE_URLS == ['']:
        logging.error("No Catalog Service URLs configured.")
        return None
    url = CATALOG_SERVICE_URLS[catalog_index]
    catalog_index = (catalog_index + 1) % len(CATALOG_SERVICE_URLS)
    return url

def get_order_service_url():
    global order_index
    if not ORDER_SERVICE_URLS or ORDER_SERVICE_URLS == ['']:
        logging.error("No Order Service URLs configured.")
        return None
    url = ORDER_SERVICE_URLS[order_index]
    order_index = (order_index + 1) % len(ORDER_SERVICE_URLS)
    return url

@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    logging.info(f"Received search request for topic: {topic}")
    cache_key = f"search:{topic}"
    if cache_key in cache:
        logging.info("Cache hit for search")
        cache.move_to_end(cache_key)
        return jsonify(cache[cache_key])
    else:
        logging.info("Cache miss for search")
        url = get_catalog_service_url()
        if not url:
            return jsonify({'error': 'No Catalog Service available'}), 503
        try:
            response = requests.get(f"{url}/search/{topic}")
            if response.status_code != 200:
                logging.error(f"Error from Catalog Service: {response.text}")
                return jsonify({'error': 'Error retrieving search results'}), response.status_code
            data = response.json()
            # Add to cache
            cache[cache_key] = data
            if len(cache) > CACHE_SIZE:
                cache.popitem(last=False)  # Remove least recently used item
            return jsonify(data)
        except Exception as e:
            logging.error(f"Error in search: {e}")
            return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    logging.info(f"Received info request for item_id: {item_id}")
    cache_key = f"info:{item_id}"
    if cache_key in cache:
        logging.info("Cache hit for info")
        cache.move_to_end(cache_key)
        return jsonify(cache[cache_key])
    else:
        logging.info("Cache miss for info")
        url = get_catalog_service_url()
        if not url:
            return jsonify({'error': 'No Catalog Service available'}), 503
        try:
            response = requests.get(f"{url}/info/{item_id}")
            if response.status_code != 200:
                logging.error(f"Error from Catalog Service: {response.text}")
                return jsonify({'error': 'Error retrieving item information'}), response.status_code
            data = response.json()
            # Add to cache
            cache[cache_key] = data
            if len(cache) > CACHE_SIZE:
                cache.popitem(last=False)
            return jsonify(data)
        except Exception as e:
            logging.error(f"Error in info: {e}")
            return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
    logging.info(f"Received purchase request for item_id: {item_id}")
    url = get_order_service_url()
    if not url:
        return jsonify({'error': 'No Order Service available'}), 503
    try:
        response = requests.put(f"{url}/purchase/{item_id}")
        if response.status_code != 200:
            logging.error(f"Error from Order Service: {response.text}")
            return jsonify({'error': 'Error processing purchase'}), response.status_code
        # Invalidate cache entries related to the item
        cache_key = f"info:{item_id}"
        if cache_key in cache:
            del cache[cache_key]
            logging.info(f"Cache invalidated for item_id: {item_id}")
        return jsonify(response.json())
    except Exception as e:
        logging.error(f"Error in purchase: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/invalidate/<int:item_id>', methods=['POST'])
def invalidate(item_id):
    """
    Endpoint to receive cache invalidation requests from backend services.
    """
    logging.info(f"Received cache invalidate request for item_id: {item_id}")
    # Invalidate 'info' cache
    cache_key_info = f"info:{item_id}"
    if cache_key_info in cache:
        del cache[cache_key_info]
        logging.info(f"Cache invalidated for key: {cache_key_info}")
    # Invalidate 'search' cache entries that may include the item
    keys_to_delete = [key for key in cache if key.startswith('search:')]
    for key in keys_to_delete:
        del cache[key]
        logging.info(f"Cache invalidated for key: {key}")
    return jsonify({'message': 'Cache invalidated'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, jsonify, request
import requests
import sqlite3
from database import init_db

app = Flask(__name__)
DATABASE = 'orders.db'
CATALOG_SERVICE_URL = 'http://catalog_service:5001'


@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            quantity INTEGER
        )
    ''')
    cursor.execute('INSERT INTO orders (item_id, quantity) VALUES (?, ?)', (item_id, 1))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Purchased item {item_id}'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002)

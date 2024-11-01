from flask import Flask, jsonify, request
import sqlite3
from database import init_db
import threading
import time

app = Flask(__name__)
DATABASE = 'catalog.db'

# Create a lock object to ensure thread safety during database operations
db_lock = threading.Lock()

def restock_items():
    """
    Background thread function that periodically increases the quantity of each book.
    """
    while True:
        time.sleep(60)  # Restock every 10 seconds
        with db_lock:
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                # Increase the quantity of each book by 5
                cursor.execute('UPDATE books SET quantity = quantity + 5')
                conn.commit()
                conn.close()
                print("Stock updated: Each item's quantity increased by 5.")
            except Exception as e:
                print(f"Error in restocking items: {e}")

@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM books WHERE topic=?', (topic,))
    books = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(books)

@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
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
    app.run(host='0.0.0.0', port=5001)

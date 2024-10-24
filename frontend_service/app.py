from flask import Flask, jsonify
import requests

app = Flask(__name__)

CATALOG_SERVICE_URL = 'http://catalog_service:5001'
ORDER_SERVICE_URL = 'http://order_service:5002'


@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    response = requests.get(f"{CATALOG_SERVICE_URL}/search/{topic}")
    return jsonify(response.json())

@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    response = requests.get(f"{CATALOG_SERVICE_URL}/info/{item_id}")
    return jsonify(response.json())

@app.route('/purchase/<int:item_id>', methods=['PUT'])
def purchase(item_id):
    response = requests.put(f"{ORDER_SERVICE_URL}/purchase/{item_id}")
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

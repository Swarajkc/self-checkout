# app.py
from flask import Flask, jsonify, render_template
import edge_detection

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_detection')
def start_detection():
    edge_detection.initialize_threads()
    return jsonify({"status": "Detection started"}), 200

@app.route('/get_details')
def get_details():
    price_per_gram = {
        "lays": 1.4,
        "coke": 0.5
    }
    weight = float(edge_detection.latest_weight.split()[-1])
    price = weight * price_per_gram.get(edge_detection.latest_object.lower(), 0)
    return jsonify({
        "object": edge_detection.latest_object,
        "weight": edge_detection.latest_weight,
        "price": f"{price:.2f} Rs"
    }), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

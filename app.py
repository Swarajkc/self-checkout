from flask import Flask, jsonify, render_template, Response
from picamera2 import Picamera2, Preview
from edge_impulse_linux.image import ImageImpulseRunner
import serial
import threading
import cv2
import numpy as np

app = Flask(__name__)

# Global variables to store the latest weight reading and detected object
latest_weight = "Waiting for data..."
latest_object = None
frame = None

# Initialize the camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (300, 300)})
picam2.configure(config)
picam2.start()

def read_from_arduino():
    global latest_weight
    ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to the correct Arduino serial port
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            latest_weight = f"Weight: {data} grams"

def object_detection():
    global latest_object, frame
    model_path = '/home/pi/modelfile.eim'  # Path to the Edge Impulse model
    runner = ImageImpulseRunner(model_path)
    runner.init()

    while True:
        frame = picam2.capture_array()
        if frame is None:
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        features, error = runner.get_features_from_image(frame_rgb)
        if not np.any(error):  # Check if no error
            results = runner.classify(features)
            if "bounding_boxes" in results['result']:
                for bbox in results['result']['bounding_boxes']:
                    latest_object = bbox['label']
                    break  # Exit after first detected object

def generate_frame():
    global frame
    while True:
        if frame is not None:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_detection')
def start_detection():
    threading.Thread(target=read_from_arduino, daemon=True).start()
    threading.Thread(target=object_detection, daemon=True).start()
    return jsonify({"status": "Detection started"}), 200

@app.route('/get_details')
def get_details():
    price_per_gram = {"Lays": 1.4, "Coke": 0.5}
    weight_str = latest_weight.split()[-1]
    try:
        weight = float(weight_str)
        price = weight * price_per_gram.get(latest_object.lower(), 0)
    except ValueError:
        weight = 0
        price = 0
    return jsonify({
        "object": latest_object,
        "weight": latest_weight,
        "price": f"{price:.2f} Rs"
    }), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

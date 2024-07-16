#!/usr/bin/env python3

import cv2
import time
import serial
from flask import Flask, render_template, jsonify, request
from edge_impulse_linux.image import ImageImpulseRunner
from picamera2 import Picamera2
from threading import Thread, Event

app = Flask(__name__)

# Setup the serial connection for weight reading
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to your Arduino port

# Global variables
products = []
model_path = '/home/pi/modelfile.eim'  # Path to your Edge Impulse model
stop_event = Event()

# Price definitions
price_per_gram = {
    'Lays': 1.21,  # NRS for 1 gram of Lays
    'Coke': 5.88   # NRS for 1 gram of Coke
}

def read_from_arduino():
    while ser.in_waiting > 0:
        data = ser.readline().decode().strip()
        try:
            weight = float(data)
            if weight > 0:
                return weight
        except ValueError:
            print("Error converting weight data to float. Data received:", data)
    return 0

def continuous_detection():
    with ImageImpulseRunner(model_path) as runner:
        runner.init()
        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
        picam2.start()

        while not stop_event.is_set():
            frame = picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            features, error = runner.get_features_from_image(frame_rgb)

            if error:
                print("Error getting features:", error)
                continue

            results = runner.classify(features)
            if "bounding_boxes" in results['result']:
                for bbox in results['result']['bounding_boxes']:
                    label = bbox['label']
                    confidence = bbox['value']
                    if confidence > 0.4:  # Threshold for detection
                        weight = read_from_arduino()
                        if weight < 5:
                            continue  # If weight is less than 5 grams, skip this detection
                        products.append({"label": label, "confidence": confidence, "weight": weight})
                        print(f"Detected {label} with confidence {confidence:.2f} and weight {weight}")
            time.sleep(1)  # Wait for a second before the next capture

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/start-detection', methods=['POST'])
def start():
    stop_event.clear()
    thread = Thread(target=continuous_detection)
    thread.start()
    return jsonify({"status": "Detection started"})

@app.route('/stop-detection', methods=['POST'])
def stop():
    stop_event.set()
    return jsonify({"status": "Detection stopped"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

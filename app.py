#!/usr/bin/env python3

import cv2
import time
import signal
import serial
from flask import Flask, render_template, jsonify, request
from edge_impulse_linux.image import ImageImpulseRunner
from picamera2 import Picamera2

app = Flask(__name__)

# Setup the serial connection for weight reading
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to your Arduino port

# Global variables
products = {}
model_path = '/home/pi/modelfile.eim'  # Path to your Edge Impulse model

# Price definitions
price_per_gram_Lays = 1.21  # NRS for 1 gram of Lays
price_per_gram_Coke = 5.88  # NRS for 1 gram of Coke

def read_from_arduino():
    weights = []
    start_time = time.time()
    while time.time() - start_time < 10:  # Read for 10 seconds
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            print(f"Raw Data from Arduino: {data}")
            try:
                weight = float(data)
                if weight > 0:
                    weights.append(weight)
            except ValueError:
                print("Error converting weight data to float. Data received:", data)    
    return weights[-1] if weights else "0"  # Return only the last value as string

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/detect', methods=['POST'])
def detect():
    weight = read_from_arduino()
    item_detected, confidence = object_detection()
    if item_detected:
        products[item_detected] = {"weight": weight, "confidence": confidence}
    return jsonify(item=item_detected, weight=weight, confidence=confidence)

@app.route('/total', methods=['POST'])
def total():
    total_price = sum(
        details['weight'] * (price_per_gram_Lays if item == 'Lays' else price_per_gram_Coke)
        for item, details in products.items()
    )
    return jsonify(total=total_price)

def object_detection():
    with ImageImpulseRunner(model_path) as runner:
        runner.init()

        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
        picam2.start()

        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        features, error = runner.get_features_from_image(frame_rgb)

        if isinstance(error, (list, tuple, dict)) and error:
            print("Error getting features:", error)
            return None, 0
        elif isinstance(error, str) and len(error) > 0:
            print("Error getting features:", error)
            return None, 0
        else:
            results = runner.classify(features)

            if "bounding_boxes" in results['result']:
                for bbox in results['result']['bounding_boxes']:
                    label = bbox['label']
                    confidence = bbox['value']
                    if confidence > 0.4:  # Threshold for detection
                        print(f"Detected {label} with confidence {confidence:.2f}")
                        return label, confidence
    return None, 0

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Run the Flask app


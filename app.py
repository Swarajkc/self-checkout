#!/usr/bin/env python3

import cv2
import serial
import time
from picamera2 import Picamera2
from edge_impulse_linux.image import ImageImpulseRunner
from flask import Flask, jsonify, render_template, Response
import threading
import numpy as np

# Setup the Flask app
app = Flask(__name__)

# Global variables to store the latest weight reading and detected object
latest_weight = "Waiting for data..."
latest_object = None
frame = None

# Setup the serial connection
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to the correct Arduino serial port

def read_from_arduino():
    global latest_weight
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            latest_weight = f"Weight: {data} grams"

def object_detection():
    global latest_object, frame
    model_path = '/home/pi/modelfile.eim'  # Path to the Edge Impulse model

    with ImageImpulseRunner(model_path) as runner:
        runner.init()

        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
        picam2.start()

        while True:
            frame = picam2.capture_array()
            if frame is None:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Ensure correct color conversion

            features, error = runner.get_features_from_image(frame_rgb)
            if isinstance(error, (list, tuple, dict)) and error:
                print("Error getting features:", error)
                continue
            elif isinstance(error, str) and len(error) > 0:
                print("Error getting features:", error)
                continue

            results = runner.classify(features)

            if "bounding_boxes" in results['result']:
                for bbox in results['result']['bounding_boxes']:
                    latest_object = bbox['label']
                    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                    cx, cy = x + w // 2, y + h // 2
                    cv2.circle(frame_rgb, (cx, cy), 5, (0, 255, 0), -1)
                    cv2.putText(frame_rgb, f"{bbox['label']}: {bbox['value']:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    print(f"Detected {bbox['label']} at ({cx}, {cy}), confidence: {bbox['value']:.2f}")
                    
                cv2.imshow('Object Detection', frame_rgb)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

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
    price_per_gram = {"lays": 1.4, "coke": 0.5}
    weight_str = latest_weight.split()[-2]  # Adjust to get numeric value correctly
    try:
        weight = float(weight_str)
        price = weight * price_per_gram.get(latest_object.lower(), 0)
    except (ValueError, AttributeError):
        weight = 0
        price = 0
    return jsonify({
        "object": latest_object,
        "weight": latest_weight,
        "price": f"{price:.2f} Rs"
    }), 200
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)


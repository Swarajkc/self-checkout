#!/usr/bin/env python3

import cv2
import serial
import time
import threading
import io
from flask import Flask, render_template, request, jsonify, Response
from picamera2 import Picamera2
from edge_impulse_linux.image import ImageImpulseRunner

# Setup the Flask application
app = Flask(__name__)

# Setup serial communication
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust as necessary for your setup

# Setup Edge Impulse
model_path = '/home/pi/modelfile.eim'  # Update this path as necessary

# Initialize global variables for the camera and runner
picam2 = Picamera2()
runner = None

# Updated product data
products = {
    "Apple": {"price": 1.00, "weight": 0},
    "Coke": {"price": 0.80, "weight": 0}
}

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/video_feed')
def video_feed():
    """Video streaming route for object detection preview."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen():
    """Video streaming generator function."""
    while True:
        frame = get_frame()
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@app.route('/detect', methods=['POST'])
def detect():
    frame = get_frame()
    try:
        features, _ = runner.get_features_from_image(frame)
        results = runner.classify(features)
        item_detected = max(results['result']['classification'], key=lambda x: x['value'])['label']
        weight = read_weight()
        response = {
            'item': item_detected,
            'price': products[item_detected]['price'],
            'weight': weight
        }
    except Exception as e:
        response = {'error': str(e)}
    return jsonify(response)

def read_weight():
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        return float(line)
    return 0.0

def get_frame():
    frame = picam2.capture_array()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame_rgb

def setup_camera():
    global runner, picam2
    runner = ImageImpulseRunner(model_path)
    runner.init()
    picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
    picam2.start()

if __name__ == '__main__':
    setup_camera()
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        picam2.stop()
        runner.close()
        ser.close()

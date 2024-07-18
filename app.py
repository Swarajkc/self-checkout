from flask import Flask, render_template, jsonify, request, redirect, url_for
import threading
import os
import cv2
import time
import serial
from edge_impulse_linux.image import ImageImpulseRunner
from picamera2 import Picamera2

app = Flask(__name__)

# Setup the serial connection for weight reading
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to your Arduino port

# Price definitions
price_per_gram_Lays = 1.21
price_per_gram_Coke = 5.88

# Global variables
products = {}  # Track detected products and their counts
model_path = '/home/pi/modelfile.eim'  # Path to your Edge Impulse model
detection_active = False
weight = 0  # Current weight reading
total_weight = {}  # Accumulate total weight for each product

# Thread for continuous object detection
def continuous_detection():
    global detection_active, products, weight, total_weight
    with ImageImpulseRunner(model_path) as runner:
        runner.init()
        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
        picam2.start()
        while detection_active:
            frame = picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            features, error = runner.get_features_from_image(frame_rgb)
            if features:
                results = runner.classify(features)
                if "bounding_boxes" in results['result']:
                    for bbox in results['result']['bounding_boxes']:
                        label = bbox['label']
                        confidence = bbox['value']
                        if confidence > 0.4:  # Threshold for detection
                            products[label] = products.get(label, 0) + 1
                            weight = read_from_arduino()  # Update weight during detection

                            # Update total weight for the detected product
                            if label in total_weight:
                                total_weight[label] += weight
                            else:
                                total_weight[label] = weight
                            break  # Only consider the first detected item

def read_from_arduino():
    global weight
    with serial_lock:
        weights = []
        start_time = time.time()
        try:
            while time.time() - start_time < 1:  # Read for a short duration
                if ser.in_waiting > 0:
                    data = ser.readline().decode().strip()
                    weight = float(data)  # Read weight from Arduino
                    if weight > 0:
                        weights.append(weight)
        except (ValueError, serial.SerialException) as e:
            print(f"Error reading from Arduino: {e}")
        return weights[-1] if weights else 0

@app.route('/')
def index():
    image_folder = 'static/images'
    images = os.listdir(image_folder)
    image_paths = [os.path.join(image_folder, img) for img in images]
    return render_template('index.html', images=image_paths)

serial_lock = threading.Lock()

@app.route('/control_detection', methods=['POST'])
def control_detection():
    global detection_active
    if request.form['action'] == 'start':
        detection_active = True
        detection_thread = threading.Thread(target=continuous_detection)
        detection_thread.start()
    elif request.form['action'] == 'stop':
        detection_active = False
    return redirect(url_for('index'))

@app.route('/get_details', methods=['GET'])
def get_details():
    global weight, total_weight
    total_price = sum(total_weight.get(item, 0) * (price_per_gram_Lays if item == 'Lays' else price_per_gram_Coke) for item in total_weight)
    return jsonify({
        'object': products,
        'weight': weight,
        'total_weight': total_weight,
        'price': total_price
    })

@app.route('/total', methods=['GET'])
def total():
    global total_weight
    total_price = sum(total_weight.get(item, 0) * (price_per_gram_Lays if item == 'Lays' else price_per_gram_Coke) for item in total_weight)
    return render_template('total.html', total=total_price, products=total_weight)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

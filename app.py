from flask import Flask, jsonify, render_template
import serial
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from edge_impulse_linux.image import ImageImpulseRunner
import threading
import numpy as np

app = Flask(__name__)

# Global variable to store the latest weight reading and detected object
latest_weight = "Waiting for data..."
latest_object = None

def read_from_arduino():
    global latest_weight
    ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to the correct Arduino serial port
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            latest_weight = f"Weight: {data} grams"

def object_detection():
    global latest_object
    model_path = '/home/pi/modelfile.eim'  # Path to the Edge Impulse model
    with ImageImpulseRunner(model_path) as runner:
        runner.init()
        picam2 = Picamera2()
        config = picam2.create_video_configuration(main={"size": (640, 480)})
        picam2.configure(config)
        picam2.start()
        
        try:
            while True:
                frame = picam2.capture_array()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                features, error = runner.get_features_from_image(frame_rgb)
                if not error:
                    results = runner.classify(features)
                    if "bounding_boxes" in results['result']:
                        for bbox in results['result']['bounding_boxes']:
                            latest_object = bbox['label']
                            break  # exit after first detected object
        finally:
            picam2.stop()  # Stop the camera when done

def initialize_threads():
    threading.Thread(target=read_from_arduino, daemon=True).start()
    threading.Thread(target=object_detection, daemon=True).start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_detection')
def start_detection():
    initialize_threads()
    return jsonify({"status": "Detection started"}), 200

@app.route('/get_details')
def get_details():
    price_per_gram = {
        "lays": 1.4,
        "coke": 0.5
    }
    weight = float(latest_weight.split()[-1])
    price = weight * price_per_gram.get(latest_object.lower(), 0)
    return jsonify({
        "object": latest_object,
        "weight": latest_weight,
        "price": f"{price:.2f} Rs"
    }), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

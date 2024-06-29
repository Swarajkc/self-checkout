# edge_detection.py
import serial
import cv2
from picamera2 import Picamera2
from edge_impulse_linux.image import ImageImpulseRunner
import threading

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
        picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
        picam2.start()

        while True:
            frame = picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            features, error = runner.get_features_from_image(frame_rgb)

            if not error:
                results = runner.classify(features)
                if "bounding_boxes" in results['result']:
                    for bbox in results['result']['bounding_boxes']:
                        latest_object = bbox['label']
                        # Assuming only one object type is detected at a time for simplicity
                        break  # exit after first detected object

def initialize_threads():
    threading.Thread(target=read_from_arduino, daemon=True).start()
    threading.Thread(target=object_detection, daemon=True).start()

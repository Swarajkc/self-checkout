import cv2
import requests
from picamera2 import Picamera2
from edge_impulse_linux.image import ImageImpulseRunner
import serial
import time
import json

# Configuration
model_path = '/home/pi/modelfile.eim'
serial_port = '/dev/ttyACM0'
server_url = 'http://<your-server-ip>:5000'

# Initialize camera and model
runner = ImageImpulseRunner(model_path)
runner.init()
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (300, 300)})
picam2.configure(config)
picam2.start()

ser = serial.Serial(serial_port, 57600)

def capture_and_process():
    while True:
        frame = picam2.capture_array()
        results = runner.classify(frame)
        if "bounding_boxes" in results['result']:
            for bbox in results['result']['bounding_boxes']:
                label = bbox['label']
                weight = read_weight()
                image_path = save_frame(frame, label)
                image_url = upload_image(image_path)
                post_data(label, weight, image_url)

def read_weight():
    if ser.in_waiting > 0:
        return int(ser.readline().decode().strip())
    return 0

def save_frame(frame, label):
    filename = f"{label}_{int(time.time())}.jpg"
    cv2.imwrite(filename, frame)
    return filename

def upload_image(image_path):
    with open(image_path, 'rb') as img:
        response = requests.post(f"{server_url}/upload_image", files={'image': img})
    return response.json()['url']

def post_data(label, weight, image_url):
    data = {'label': label, 'weight': weight, 'total_price': weight * 0.5, 'url': image_url}  # Example price calculation
    requests.post(f"{server_url}/add_item", json=data)

capture_and_process()


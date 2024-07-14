from flask import Flask, render_template, request, jsonify, Response
import picamera
import io
import serial
import time
import threading
import edge_impulse_linux.image as ei_image

app = Flask(__name__)

# Setup Edge Impulse
model = ei_image.Classifier('/home/pi/modelfile.eim')  # Update this path as necessary

# Setup Serial Communication
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust as necessary for your setup

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
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/detect', methods=['POST'])
def detect():
    frame = Camera().get_frame()
    try:
        prediction = model.classify(frame)
        item_detected = prediction['result']['classification']
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
    ser.write(b'w')
    line = ser.readline().decode('utf-8').strip()
    return float(line)

class Camera(object):
    def __init__(self):
        self.camera = picamera.PiCamera()
        self.camera.resolution = (300, 300)
        self.camera.framerate = 24
        time.sleep(2)

    def __del__(self):
        self.camera.close()

    def get_frame(self):
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg')
        stream.seek(0)
        return stream.read()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

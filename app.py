from flask import Flask, render_template, request, jsonify, Response
import cv2
import serial
import time
from picamera2 import Picamera2
from edge_impulse_linux.image import ImageImpulseRunner

app = Flask(__name__)
ser = serial.Serial('/dev/ttyACM0', 57600)
model_path = '/home/pi/modelfile.eim'
picam2 = None
runner = None

products = {
    "Apple": {"price": 1.00, "weight": 0},
    "Coke": {"price": 0.80, "weight": 0}
}

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen():
    while True:
        frame = get_frame()
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

def get_frame():
    global picam2
    if not picam2:
        setup_camera()
    frame = picam2.capture_array()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame_rgb

def setup_camera():
    global picam2, runner
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"size": (300, 300)}))
        picam2.start()
        runner = ImageImpulseRunner(model_path)
        runner.init()
    except Exception as e:
        print("Failed to initialize camera:", str(e))

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    global picam2, runner, ser
    if picam2:
        picam2.stop()
    if runner:
        runner.stop()  # Adjusting the method to stop the runner
    if ser:
        ser.close()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()

if __name__ == '__main__':
    try:
        setup_camera()
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        shutdown_server()

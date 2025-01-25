from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import os
import time
import sqlite3
import serial
from edge_impulse_linux.image import ImageImpulseRunner
import cv2
import RPi.GPIO as GPIO
import qrcode
import urllib.parse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Path to Edge Impulse model
model_path = '/home/pi/model.eim'

# Serial connection for weight reading
ser = serial.Serial('/dev/ttyACM0', 57600)  # Adjust to your Arduino port

# Conveyor Motor GPIO Pins
MotorA_EN = 18
MotorA_IN1 = 20
MotorA_IN2 = 21
MotorB_EN = 23
MotorB_IN1 = 22
MotorB_IN2 = 27

# Servo Motor GPIO Pin
SERVO_PIN = 17

# Global variables
detection_active = False
item_detected = None
weight = 0
products = {}
serial_lock = threading.Lock()
last_detected_item = None
last_detection_time = 0
DETECTION_TIMEOUT = 2
transactions = {}
PAYMENT_TIMEOUT = 120

# Updated Mock Payment Base
MOCK_PAYMENT_BASE = "http://192.168.218.239:5000/mock_payment"

# Setup Conveyor GPIO
def setup_conveyor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(MotorA_EN, GPIO.OUT)
    GPIO.setup(MotorA_IN1, GPIO.OUT)
    GPIO.setup(MotorA_IN2, GPIO.OUT)
    GPIO.setup(MotorB_EN, GPIO.OUT)
    GPIO.setup(MotorB_IN1, GPIO.OUT)
    GPIO.setup(MotorB_IN2, GPIO.OUT)
    global pwmA, pwmB
    pwmA = GPIO.PWM(MotorA_EN, 100)
    pwmB = GPIO.PWM(MotorB_EN, 100)
    pwmA.start(0)
    pwmB.start(0)

    GPIO.setup(SERVO_PIN, GPIO.OUT)
    global servo_pwm
    servo_pwm = GPIO.PWM(SERVO_PIN, 50)
    servo_pwm.start(0)

def set_servo_angle(angle):
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo_pwm.ChangeDutyCycle(0)

def start_conveyor():
    pwmA.ChangeDutyCycle(50)
    pwmB.ChangeDutyCycle(50)
    GPIO.output(MotorA_IN1, GPIO.HIGH)
    GPIO.output(MotorA_IN2, GPIO.LOW)
    GPIO.output(MotorB_IN1, GPIO.HIGH)
    GPIO.output(MotorB_IN2, GPIO.LOW)

def stop_conveyor():
    pwmA.ChangeDutyCycle(0)
    pwmB.ChangeDutyCycle(0)
    GPIO.output(MotorA_IN1, GPIO.LOW)
    GPIO.output(MotorA_IN2, GPIO.LOW)
    GPIO.output(MotorB_IN1, GPIO.LOW)
    GPIO.output(MotorB_IN2, GPIO.LOW)

def cleanup_conveyor():
    pwmA.stop()
    pwmB.stop()
    servo_pwm.stop()
    GPIO.cleanup()

def get_db_connection():
    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_price(item, weight):
    if item in ['blue_lays', 'green_lays']:
        return 50 if weight < 70 else 80
    elif item in ['coke', 'fanta']:
        return 50 if weight < 500 else 100
    elif item == 'waiwai':
        return 20
    return 0

def read_from_arduino():
    global weight
    with serial_lock:
        weights = []
        start_time = time.time()
        while time.time() - start_time < 2:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                try:
                    current_weight = float(data)
                    if current_weight >= 0:
                        weights.append(current_weight)
                except ValueError:
                    pass
        weight = max(weights) if weights else 0

def continuous_detection():
    global detection_active, item_detected, weight, last_detected_item, last_detection_time
    with ImageImpulseRunner(model_path) as runner:
        runner.init()
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return

        no_detection_start_time = None  # Track time when no item is detected
        item_locked = False  # Flag to lock detection while an item is being processed

        while detection_active:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (300, 300))
            features, error = runner.get_features_from_image(frame_resized)
            if features:
                results = runner.classify(features)
                if "bounding_boxes" in results['result']:
                    detected_this_frame = False
                    for bbox in results['result']['bounding_boxes']:
                        label = bbox['label']
                        confidence = bbox['value']

                        if confidence > 0.4:  # Confidence threshold
                            current_time = time.time()

                            if not item_locked:
                                # If sufficient time has passed since the last detection or it's a new item
                                if (
                                    label != last_detected_item
                                    or (current_time - last_detection_time > 3)  # 3-second timeout
                                ):
                                    products[label] = products.get(label, 0) + 1
                                    last_detected_item = label
                                    last_detection_time = current_time
                                    item_detected = label
                                    item_locked = True  # Lock the detection for processing

                                detected_this_frame = True
                                # Reset no-detection timer
                                no_detection_start_time = None
                            break  # Process only one item at a time

                if not detected_this_frame:
                    # No item detected in this frame
                    if no_detection_start_time is None:
                        no_detection_start_time = time.time()
                    elif time.time() - no_detection_start_time > 3:
                        # Unlock the item detection after 3 seconds of no detection
                        item_detected = None
                        last_detected_item = None
                        item_locked = False

            read_from_arduino()  # Ensure weight reading continues

        cap.release()

def generate_mock_qr(amount, transaction_id, output_path='static/mock_qr.png'):
    """Generate a QR code for mock payment."""
    # Ensure the URL points to the mock payment route
    payment_url = url_for('mock_payment', amt=amount, pid=transaction_id, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=2,
    )
    qr.add_data(payment_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    return output_path

@app.route('/get_stock', methods=['GET'])
def get_stock():
    conn = get_db_connection()
    stocks = conn.execute('SELECT * FROM stocks').fetchall()
    conn.close()

    stock_list = [{'item_name': stock['item_name'], 'quantity': stock['quantity']} for stock in stocks]
    return jsonify(stock_list)

@app.route('/get_details', methods=['GET'])
def get_details():
    global item_detected, weight, products
    detected_images = [f'images/{item}.jpg' for item in products.keys()]
    price = calculate_price(item_detected, weight) if item_detected else 0
    return jsonify({
        'object': item_detected,
        'weight': weight,
        'price': price,
        'detected_images': detected_images
    })

@app.route('/')
def index():
    global item_detected, products, weight

    detected_image = None
    if item_detected:
        detected_image = os.path.join('images', f"{item_detected}.jpg")

    conn = get_db_connection()
    stocks = conn.execute('SELECT * FROM stocks').fetchall()
    conn.close()

    return render_template(
        'index.html',
        stocks=stocks,
        detected_image=detected_image,
        item_detected=item_detected
    )

@app.route('/total', methods=['GET'])
def total():
    global products
    total_price = sum(calculate_price(item, weight) * count for item, count in products.items())
    return render_template('total.html', total=total_price, products=products)

@app.route('/generate_payment_qr', methods=['GET'])
def generate_payment_qr():
    global products, transactions
    # Calculate the total price
    total_price = sum(calculate_price(item, weight) * count for item, count in products.items())
    transaction_id = f"TXN-{int(time.time())}"  # Unique transaction ID
    qr_path = generate_mock_qr(total_price, transaction_id)  # Generate QR code
    transactions[transaction_id] = time.time()  # Store the transaction with a timestamp

    # Emit the transaction details for coordination with the frontend
    socketio.emit('qr_generated', {
        'qr_path': qr_path,
        'total_price': total_price,
        'transaction_id': transaction_id
    })

    # Render the QR code page with transaction details
    return render_template(
        'payment_qr.html',
        qr_path=qr_path,
        total_price=total_price,
        transaction_id=transaction_id
    )

@app.route('/mock_payment', methods=['GET', 'POST'])
def mock_payment():
    if request.method == 'GET':
        amount = request.args.get('amt')  # Fetch total amount
        transaction_id = request.args.get('pid')  # Fetch transaction ID
        return render_template('mock_payment.html', amount=amount, transaction_id=transaction_id)
    elif request.method == 'POST':
        action = request.form.get('action')  # Handle success or failure
        transaction_id = request.form.get('transaction_id')
        amount = request.form.get('amount')
        if action == 'success':
            socketio.emit('payment_status', {'status': 'success', 'amount': amount})
            return redirect(url_for('payment_success', amt=amount, oid=transaction_id))
        elif action == 'failure':
            socketio.emit('payment_status', {'status': 'failure'})
            return redirect(url_for('payment_failure', message="Payment failed!"))

@app.route('/payment_success', methods=['GET'])
def payment_success():
    global products, weight, item_detected, transactions

    amount = request.args.get('amt')  # Total amount from the URL parameter
    transaction_id = request.args.get('oid')  # Transaction ID

    if transaction_id in transactions and time.time() - transactions[transaction_id] <= PAYMENT_TIMEOUT:
        # Update stock in the database
        conn = get_db_connection()
        for item, count in products.items():
            conn.execute(
                'UPDATE stocks SET quantity = quantity - ? WHERE item_name = ? AND quantity >= ?',
                (count, item, count)
            )
        conn.commit()
        conn.close()

        # Clear data after successful payment
        products.clear()
        weight = 0
        item_detected = None
        transactions.pop(transaction_id, None)

        # Servo movement to simulate dispensing items
        set_servo_angle(90)
        time.sleep(10)
        set_servo_angle(0)

        return render_template('payment_success.html', total_price=amount)

    return render_template('payment_failure.html', message="Transaction timeout or ID mismatch.")

@app.route('/payment_failure', methods=['GET'])
def payment_failure():
    return render_template('payment_failure.html', message=request.args.get('message', "Payment failed."))

@app.route('/control_detection', methods=['POST'])
def control_detection():
    global detection_active
    if request.form['action'] == 'start':
        detection_active = True
        set_servo_angle(90)
        start_conveyor()
        threading.Thread(target=continuous_detection).start()
    elif request.form['action'] == 'stop':
        detection_active = False
        stop_conveyor()
        set_servo_angle(0)
    return redirect(url_for('index'))

@socketio.on('payment_completed')
def payment_completed(data):
    transaction_id = data.get('transaction_id')
    if transaction_id in transactions and time.time() - transactions[transaction_id] <= PAYMENT_TIMEOUT:
        transactions.pop(transaction_id, None)
        set_servo_angle(90)
        time.sleep(10)
        set_servo_angle(0)
        socketio.emit('payment_status', {'status': 'success'})
    else:
        socketio.emit('payment_status', {'status': 'failure'})

if __name__ == "__main__":
    setup_conveyor()
    try:
        socketio.run(app, host='0.0.0.0', port=5000)
    finally:
        cleanup_conveyor()

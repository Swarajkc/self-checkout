# Self-Checkout System

This project is a Raspberry Pi-powered self-checkout system built to replace traditional cashiers in retail environments. It integrates real-time object detection, weight-based pricing, and a mock payment system — all managed via a locally hosted Flask web interface.

---

## Features

- **Real-Time Object Detection** using the FOMO model via Edge Impulse.
- **Automatic Weight Calculation** using HX711 load cell and Arduino Uno.
- **Inventory Management** with SQLite — stock auto-decrements after purchase.
- **Web Interface** using Flask, HTML/CSS, and JS.
- **Mock Payment Gateway** with QR code and simulated confirmation.
- **Conveyor Belt Integration** for auto-bagging after successful payment.

---

## Tech Stack

- **Raspberry Pi** (Main controller)
- **Arduino Uno + HX711** (Weight sensor module)
- **Edge Impulse FOMO** (Object Detection model)
- **Flask and Python** (Backend server)
- **SQLite** (Local product stock DB)
- **HTML/CSS/JS** (Frontend interface)

---

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Swarajkc/self-checkout.git
   cd self-checkout

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Database**

   ```bash
   python setup_db.py
   ```

4. **Connect Hardware**

   * Ensure your **Arduino Uno** is connected via USB to the Raspberry Pi.
   * Attach your **HX711 + Load Cell** to Arduino.
   * Your **Edge Impulse .eim model** (`modelfile.eim`) should be ready.

---

## Usage

1. **Start the Flask App**

   ```bash
   python app.py
   ```

2. **Access Web UI**
   Visit `http://localhost:5000` in your browser.

3. **Workflow**

   * Start object detection via the web interface.
   * Detected item and its weight is recorded.
   * The total price is calculated.
   * Scan QR code to simulate payment.
   * If payment is confirmed, items are bagged via a **conveyor belt**.

---

## Configuration Notes

* Update serial port settings in `app.py` to match your Arduino's port.
* Modify product info or images via:

  * `static/images/`
  * `setup_db.py` for initial database stock setup

---

## Sample Products

Product images are located in `static/images/`:

* Coke
* Fanta
* Green Lays
* Blue Lays
* Wai Wai

---

## Contributing

Pull requests and feature ideas are welcome! Fork the repo and submit your changes to `main`.

---

## License

This project is licensed under the **MIT License**.

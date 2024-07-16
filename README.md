# Self-Checkout System

This project is a Flask-based self-checkout system designed for retail environments, enabling automated object detection and pricing calculations.

## Features

- **Real-Time Object Detection**: Leverages machine learning to identify products.
- **Dynamic Pricing Calculation**: Computes prices based on detected objects and their weights.
- **Interactive Web Interface**: Start and stop detection, view detected items, and proceed to checkout through a web interface.

## Technology Stack

- Flask
- Python
- Edge Impulse (for object detection)
- PiCamera / OpenCV (for handling image data)
- HTML/CSS for the front end

## Installation

1. Clone this repository:
 git clone https://github.com/Swarajkc/self-checkout.git
2. Navigate to the project directory:
cd self-checkout-system
3. Install required Python packages:

## Usage

To start the application, run:


Visit `http://localhost:5000` in your web browser to interact with the application.

## Configuration

- Adjust the `app.py` to point to your specific hardware setup, e.g., the serial port for Arduino.
- Place images in the `static/images` directory to be displayed on the web interface.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests to the main branch.

## License

This project is licensed under the [MIT License](LICENSE).

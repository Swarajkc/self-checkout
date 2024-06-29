from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), nullable=False)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    file = request.files['image']
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({"url": file_path}), 200

@app.route('/add_item', methods=['POST'])
def add_item():
    data = request.get_json()
    new_item = Item(name=data['label'], weight=data['weight'], price=data['total_price'], image_url=data['url'])
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"status": "success", "item_id": new_item.id}), 200

@app.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)

if __name__ == "__main__":
    db.create_all()
    app.run(host='0.0.0.0', port=5000)

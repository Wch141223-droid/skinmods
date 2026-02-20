import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))
    balance = db.Column(db.Integer, default=1000)
    is_admin = db.Column(db.Boolean, default=False)

class Skin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    image = db.Column(db.String(200))
    stock = db.Column(db.Integer, default=10)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    skin_id = db.Column(db.Integer)
    price = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    skins = Skin.query.all()
    user = User.query.get(session['user_id'])
    return render_template('index.html', skins=skins, user=user)

@app.route('/buy/<int:skin_id>')
def buy(skin_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    skin = Skin.query.get(skin_id)

    if not skin or skin.stock <= 0:
        return "商品不存在或库存不足"

    existing = Order.query.filter_by(user_id=user.id, skin_id=skin.id).first()
    if existing:
        return "你已经购买过该皮肤"

    if user.balance < skin.price:
        return "余额不足"

    user.balance -= skin.price
    skin.stock -= 1

    order = Order(user_id=user.id, skin_id=skin.id, price=skin.price)
    db.session.add(order)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password_hash=password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

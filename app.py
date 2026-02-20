import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

class Skin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.String(50))
    image = db.Column(db.String(200))
    description = db.Column(db.Text)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    username = db.Column(db.String(100))
    skin_id = db.Column(db.Integer)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    skins = Skin.query.all()
    return render_template('index.html', skins=skins, username=session['username'])

@app.route('/skin/<int:skin_id>')
def skin_detail(skin_id):
    skin = Skin.query.get_or_404(skin_id)
    comments = Comment.query.filter_by(skin_id=skin_id).all()
    return render_template('skin_detail.html', skin=skin, comments=comments)

@app.route('/comment/<int:skin_id>', methods=['POST'])
def comment(skin_id):
    if 'username' in session:
        content = request.form['content']
        new_comment = Comment(content=content, username=session['username'], skin_id=skin_id)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('skin_detail', skin_id=skin_id))

@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user.is_admin:
        return "无权限"

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        skin = Skin(name=name, price=price, description=description, image="uploads/"+filename)
        db.session.add(skin)
        db.session.commit()

    skins = Skin.query.all()
    return render_template('admin.html', skins=skins)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

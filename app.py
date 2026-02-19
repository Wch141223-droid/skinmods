import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/skins'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.environ.get("EMAIL_PASS")

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
mail = Mail(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    content = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    comments = Comment.query.all()
    return render_template('index.html', comments=comments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('邮箱已注册')
            return redirect(url_for('register'))
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        msg = Message('注册成功', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'{username}，恭喜你注册成功！'
        mail.send(msg)
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        flash('邮箱或密码错误')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload_skin', methods=['POST'])
@login_required
def upload_skin():
    if 'skin' not in request.files:
        flash('未选择文件')
        return redirect(url_for('index'))
    file = request.files['skin']
    if file.filename == '':
        flash('未选择文件')
        return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    flash('皮肤上传成功')
    return redirect(url_for('index'))

@app.route('/comment', methods=['POST'])
@login_required
def comment():
    content = request.form['content']
    new_comment = Comment(username=current_user.username, content=content)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/skins/<filename>')
def skins(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8080)

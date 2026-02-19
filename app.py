import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
import random, string

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skinmods.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.environ.get("EMAIL_PASS")

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    username = db.Column(db.String(50), default="新用户")
    is_developer = db.Column(db.Boolean, default=False)

class Skin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    content = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

verification_codes = {}

@app.route("/")
def home():
    skins = Skin.query.all()
    return render_template("index.html", skins=skins, current_user=current_user)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if User.query.filter_by(email=email).first():
            flash("邮箱已注册")
            return redirect(url_for("register"))
        code = ''.join(random.choices(string.digits, k=6))
        verification_codes[email] = code
        msg = Message("SkinMods 验证码", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"你的验证码是: {code}"
        mail.send(msg)
        flash("验证码已发送到邮箱")
        return render_template("verify.html", email=email, password=password)
    return render_template("register.html")

@app.route("/verify", methods=["POST"])
def verify():
    email = request.form["email"]
    password = request.form["password"]
    code_input = request.form["code"]
    if verification_codes.get(email) == code_input:
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("注册成功，请登录")
        return redirect(url_for("login"))
    flash("验证码错误")
    return redirect(url_for("register"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("home"))
        flash("邮箱或密码错误")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST" and "file" in request.files:
        f = request.files["file"]
        filepath = os.path.join("static/skins", f.filename)
        f.save(filepath)
        skin = Skin(filename=f.filename, uploader_id=current_user.id)
        db.session.add(skin)
        current_user.is_developer = True
        db.session.commit()
        flash("上传成功，开发者头衔已获得")
        return redirect(url_for("home"))
    return render_template("upload.html")

@app.route("/comment", methods=["POST"])
def comment():
    user = request.form["user"]
    content = request.form["content"]
    new_comment = Comment(user=user, content=content)
    db.session.add(new_comment)
    db.session.commit()
    flash("评论成功")
    return redirect(url_for("home"))

@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

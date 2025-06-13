from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("Kullanıcı adı ve şifre boş olamaz.", "error")
            return redirect(url_for("auth.register"))

        db = get_db()

        existing_user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if existing_user:
            flash("Bu kullanıcı adı zaten kayıtlı.", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        db.commit()

        flash("Kayıt başarılı! Giriş yapabilirsin.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            session["user_id"] = user["id"]
            flash("Giriş başarılı!", "success")
            return redirect(url_for("notes.home"))
        else:
            flash("Kullanıcı adı veya şifre yanlış.", "error")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız.", "success")
    return redirect(url_for("auth.login"))

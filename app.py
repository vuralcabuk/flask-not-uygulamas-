from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from flask import g
from flask import Flask, render_template, request, session, flash, redirect, url_for


app = Flask(__name__)

app.secret_key = os.urandom(24)


DATABASE = "database.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Kolonlara isimle erişmek için
        # Kullanıcılar tablosunu oluştur (eğer yoksa)
        cursor = g.db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)

        # Notlar tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)

        g.db.commit() # Değişiklikleri kaydet
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def home():
    if "username" not in session:
        flash("Lütfen önce giriş yapın.", "error")
        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":
        content = request.form["content"]
        if content.strip():
            db.execute(
                "INSERT INTO notes (user_id, content) VALUES (?, ?)",
                (session["user_id"], content)
            )
            db.commit()
            flash("Not başarıyla eklendi.", "success")
        else:
            flash("Not boş olamaz.", "error")

    notes = db.execute(
        "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()

    return render_template("index.html", username=session["username"], notes=notes)

@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if "user_id" not in session:
        flash("Yetkisiz erişim.", "error")
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    )
    db.commit()
    flash("Not silindi.", "success")
    return redirect(url_for("home"))

@app.route("/edit_note/<int:note_id>")
def edit_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    note = db.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    ).fetchone()

    if note is None:
        flash("Not bulunamadı.", "error")
        return redirect(url_for("home"))

    return render_template("edit_note.html", note=note)

@app.route("/update_note/<int:note_id>", methods=["POST"])
def update_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    content = request.form["content"]
    if not content.strip():
        flash("Not boş olamaz.", "error")
        return redirect(url_for("edit_note", note_id=note_id))

    db = get_db()
    db.execute(
        "UPDATE notes SET content = ? WHERE id = ? AND user_id = ?",
        (content, note_id, session["user_id"])
    )
    db.commit()
    flash("Not güncellendi.", "success")
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/notes")
def notes():
    return render_template("notes.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("Kullanıcı adı ve şifre boş olamaz.", "error")
            return redirect(url_for("register"))

        db = get_db()

        # Kullanıcı var mı kontrol et
        existing_user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing_user:
            flash("Bu kullanıcı adı zaten kayıtlı.", "error")
            return redirect(url_for("register"))

        # 🔐 Şifreyi hashle
        hashed_password = generate_password_hash(password)

        # Veritabanına kayıt
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        db.commit()

        flash("Kayıt başarılı! Şimdi giriş yapabilirsin.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            session["user_id"] = user["id"]
            flash("Giriş başarılı!", "success")
            return redirect(url_for("home"))
        else:
            flash("Kullanıcı adı veya şifre yanlış.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()  # Tüm oturum verilerini temizler
    flash("Başarıyla çıkış yaptınız.", "success")
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)

from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from db import get_db

notes = Blueprint("notes", __name__)

@notes.route("/", methods=["GET", "POST"])
@notes.route("/index", methods=["GET", "POST"])
def home():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        if content and content.strip():
            db.execute(
                "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
                (session["user_id"], title, content)
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

@notes.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    if "user_id" not in session:
        flash("Yetkisiz erişim.", "error")
        return redirect(url_for("auth.login"))

    db = get_db()
    db.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    )
    db.commit()
    flash("Not silindi.", "success")
    return redirect(url_for("notes.home"))

@notes.route("/edit_note/<int:note_id>")
def edit_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    note = db.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    ).fetchone()

    if note is None:
        flash("Not bulunamadı.", "error")
        return redirect(url_for("notes.home"))

    return render_template("edit_note.html", note=note)

@notes.route("/update_note/<int:note_id>", methods=["POST"])
def update_note(note_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    content = request.form.get("content")
    if not content or not content.strip():
        flash("Not boş olamaz.", "error")
        return redirect(url_for("notes.edit_note", note_id=note_id))

    db = get_db()
    db.execute(
        "UPDATE notes SET content = ? WHERE id = ? AND user_id = ?",
        (content, note_id, session["user_id"])
    )
    db.commit()
    flash("Not güncellendi.", "success")
    return redirect(url_for("notes.home"))

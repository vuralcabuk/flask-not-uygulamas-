from flask import Flask, render_template
import os

from auth.routes import auth
from notes.routes import notes
from db import close_db

app = Flask(__name__)
app.register_blueprint(auth)
app.register_blueprint(notes)

app.secret_key = os.urandom(24)

@app.teardown_appcontext
def teardown(error):
    close_db(error)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/notes")
def notes():
    return render_template("notes.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(debug=True)

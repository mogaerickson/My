import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")

# SQLite is suitable for local development. Serverless deployments such as Vercel
# have ephemeral filesystems; use a hosted database for persistent production data.
DATABASE = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "questbound.db"))
Path(DATABASE).parent.mkdir(parents=True, exist_ok=True)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL,
        class TEXT NOT NULL,
        level INTEGER NOT NULL DEFAULT 1,
        xp INTEGER NOT NULL DEFAULT 0,
        hp INTEGER NOT NULL DEFAULT 100,
        coins INTEGER NOT NULL DEFAULT 50,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    character = None
    if "user_id" in session:
        character = db().execute(
            "SELECT * FROM characters WHERE user_id = ?", (session["user_id"],)
        ).fetchone()
    return render_template("index.html", character=character)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not (3 <= len(username) <= 30) or len(password) < 8:
            flash("Username must be 3–30 characters and password at least 8 characters.", "error")
            return render_template("register.html")
        try:
            db().execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            db().commit()
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("index"))


@app.route("/character", methods=["GET", "POST"])
@login_required
def character():
    existing = db().execute(
        "SELECT * FROM characters WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    if existing:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        char_class = request.form.get("class", "")
        if not (2 <= len(name) <= 18) or char_class not in ("Warrior", "Mage", "Archer"):
            flash("Choose a 2–18 character name and a valid class.", "error")
            return render_template("character.html")
        db().execute(
            "INSERT INTO characters (user_id, name, class) VALUES (?, ?, ?)",
            (session["user_id"], name, char_class)
        )
        db().commit()
        flash("Your adventurer is ready!", "success")
        return redirect(url_for("index"))
    return render_template("character.html")


@app.route("/adventure")
@login_required
def adventure():
    character = db().execute(
        "SELECT * FROM characters WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    if not character:
        return redirect(url_for("character"))
    return render_template("adventure.html", character=character)


# Initialize tables when the app is imported by a WSGI/serverless host.
init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )

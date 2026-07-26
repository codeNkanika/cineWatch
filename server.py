"""
server.py
---------
Flask app that does three jobs:
  1. Serves the static frontend (index.html, watchlist.html, style.css, app.js, login.html, signup.html)
  2. Exposes a small JSON REST API under /api/* backed by PostgreSQL (db.py)
  3. Handles accounts (signup/login/logout) with Flask-Login, so every
     watchlist item is private to the account that created it.
 
Run with:  python server.py
"""
 
import os
 
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from psycopg2 import errors as pg_errors
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
 
import db
 
load_dotenv()
 
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app, supports_credentials=True)
 
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. Add a random SECRET_KEY value to your .env "
        "(locally) and to your Render environment variables (in production)."
    )
 
VALID_STATUSES = {"want_to_watch", "watching", "watched"}
VALID_TYPES = {"movie", "tv"}
 
# ---------------------------------------------------------------------
# Flask-Login setup
# ---------------------------------------------------------------------
 
login_manager = LoginManager()
login_manager.init_app(app)
 
 
class User(UserMixin):
    """Thin wrapper so Flask-Login can track who's logged in via the session cookie."""
 
    def __init__(self, row):
        self.id = row["id"]
        self.email = row["email"]
 
 
@login_manager.user_loader
def load_user(user_id):
    row = db.get_user_by_id(int(user_id))
    return User(row) if row else None
 
 
@login_manager.unauthorized_handler
def unauthorized():
    # API calls get a JSON 401 (so app.js can redirect to /login itself)
    # instead of Flask-Login's default HTML redirect.
    return jsonify({"error": "login required"}), 401
 
 
# ---------------------------------------------------------------------
# Frontend routes (static pages)
# ---------------------------------------------------------------------
 
@app.route("/")
def home():
    return send_from_directory(".", "index.html")
 
 
@app.route("/watchlist.html")
@app.route("/watchlist")
def watchlist_page():
    return send_from_directory(".", "watchlist.html")
 
 
@app.route("/login.html")
@app.route("/login")
def login_page():
    return send_from_directory(".", "login.html")
 
 
@app.route("/signup.html")
@app.route("/signup")
def signup_page():
    return send_from_directory(".", "signup.html")
 
 
# ---------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------
 
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
 
    if not email or "@" not in email:
        return jsonify({"error": "a valid email is required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
 
    if db.get_user_by_email(email) is not None:
        return jsonify({"error": "an account with that email already exists"}), 409
 
    password_hash = generate_password_hash(password)
    row = db.create_user(email, password_hash)
    login_user(User({"id": row["id"], "email": row["email"]}))
    return jsonify({"id": row["id"], "email": row["email"]}), 201
 
 
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
 
    row = db.get_user_by_email(email)
    if row is None or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "invalid email or password"}), 401
 
    login_user(User(row))
    return jsonify({"id": row["id"], "email": row["email"]})
 
 
@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})
 
 
@app.route("/api/me")
def me():
    if current_user.is_authenticated:
        return jsonify({"id": current_user.id, "email": current_user.email})
    return jsonify(None)
 
 
# ---------------------------------------------------------------------
# Watchlist API — every route below requires login, and every db.py call
# passes current_user.id so a user can only ever see/edit their own rows.
# ---------------------------------------------------------------------
 
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})
 
 
@app.route("/api/stats")
@login_required
def stats():
    return jsonify(db.get_stats(current_user.id))
 
 
@app.route("/api/items", methods=["GET"])
@login_required
def get_items():
    status = request.args.get("status")
    if status and status not in VALID_STATUSES:
        return jsonify({"error": f"invalid status '{status}'"}), 400
    return jsonify(db.list_items(current_user.id, status=status))
 
 
@app.route("/api/items", methods=["POST"])
@login_required
def add_item():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    media_type = (data.get("media_type") or "movie").strip()
    notes = (data.get("notes") or "").strip()
 
    if not title:
        return jsonify({"error": "title is required"}), 400
    if media_type not in VALID_TYPES:
        return jsonify({"error": f"media_type must be one of {sorted(VALID_TYPES)}"}), 400
 
    item = db.create_item(current_user.id, title, media_type, notes)
    return jsonify(item), 201
 
 
@app.route("/api/items/<int:item_id>", methods=["PATCH"])
@login_required
def edit_item(item_id):
    if db.get_item(current_user.id, item_id) is None:
        return jsonify({"error": "item not found"}), 404
 
    data = request.get_json(silent=True) or {}
    updates = {}
 
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        updates["title"] = title
 
    if "media_type" in data:
        if data["media_type"] not in VALID_TYPES:
            return jsonify({"error": f"media_type must be one of {sorted(VALID_TYPES)}"}), 400
        updates["media_type"] = data["media_type"]
 
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400
        updates["status"] = data["status"]
 
    if "rating" in data:
        rating = data["rating"]
        if rating is not None and rating not in (1, 2, 3, 4, 5):
            return jsonify({"error": "rating must be 1-5 or null"}), 400
        updates["rating"] = rating
 
    if "notes" in data:
        updates["notes"] = (data["notes"] or "").strip()
 
    try:
        item = db.update_item(current_user.id, item_id, **updates)
    except pg_errors.CheckViolation:
        return jsonify({"error": "invalid field value"}), 400
 
    return jsonify(item)
 
 
@app.route("/api/items/<int:item_id>", methods=["DELETE"])
@login_required
def remove_item(item_id):
    deleted = db.delete_item(current_user.id, item_id)
    if deleted is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify({"deleted": deleted["id"]})
 
 
# Initialize the DB connection pool and tables whenever this module is
# imported — this runs both under `python server.py` (local dev) and under
# gunicorn (production hosting like Render), since gunicorn imports the
# module rather than executing the __main__ block below.
db.init_pool()
db.init_db()
 
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"\n🕯️  Cozy Watchlist running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", debug=debug, port=port)

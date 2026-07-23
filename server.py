"""
server.py
---------
Flask app that does two jobs:
  1. Serves the static frontend (index.html, watchlist.html, style.css, app.js)
  2. Exposes a small JSON REST API under /api/* backed by PostgreSQL (db.py)

Run with:  python server.py
"""

import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from psycopg2 import errors as pg_errors
from dotenv import load_dotenv

import db

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

VALID_STATUSES = {"want_to_watch", "watching", "watched"}
VALID_TYPES = {"movie", "tv"}


# ---------------------------------------------------------------------
# Frontend routes
# ---------------------------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/watchlist.html")
@app.route("/watchlist")
def watchlist_page():
    return send_from_directory(".", "watchlist.html")


# ---------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/stats")
def stats():
    return jsonify(db.get_stats())


@app.route("/api/items", methods=["GET"])
def get_items():
    status = request.args.get("status")
    if status and status not in VALID_STATUSES:
        return jsonify({"error": f"invalid status '{status}'"}), 400
    return jsonify(db.list_items(status=status))


@app.route("/api/items", methods=["POST"])
def add_item():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    media_type = (data.get("media_type") or "movie").strip()
    notes = (data.get("notes") or "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400
    if media_type not in VALID_TYPES:
        return jsonify({"error": f"media_type must be one of {sorted(VALID_TYPES)}"}), 400

    item = db.create_item(title, media_type, notes)
    return jsonify(item), 201


@app.route("/api/items/<int:item_id>", methods=["PATCH"])
def edit_item(item_id):
    if db.get_item(item_id) is None:
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
        item = db.update_item(item_id, **updates)
    except pg_errors.CheckViolation:
        return jsonify({"error": "invalid field value"}), 400

    return jsonify(item)


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def remove_item(item_id):
    deleted = db.delete_item(item_id)
    if deleted is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify({"deleted": deleted["id"]})


if __name__ == "__main__":
    db.init_pool()
    db.init_db()
    port = int(os.getenv("PORT", 5000))
    print(f"\n🕯️  Cozy Watchlist running at http://localhost:{port}\n")
    app.run(debug=True, port=port)

"""
CineWatch API server.

Thin Flask layer over db.py — every route just calls one of the existing
functions (add_movie, view_movies, mark_watched, rate_movie, delete_movie)
that your teammate already wrote, plus a couple of small additions
(get_movie, mark_watchlist, notes/poster support) needed for a richer UI.

Run:
    pip install -r requirements.txt
    python server.py
Then open http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import db

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

db.init_db()


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/movies", methods=["GET"])
def api_view_movies():
    return jsonify(db.view_movies())


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def api_get_movie(movie_id):
    movie = db.get_movie(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify(movie)


@app.route("/api/movies", methods=["POST"])
def api_add_movie():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    genre = (data.get("genre") or "").strip()
    poster_url = (data.get("poster_url") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None

    if not title:
        return jsonify({"error": "Title is required"}), 400

    movie = db.add_movie(title, genre, poster_url, notes)
    return jsonify(movie), 201


@app.route("/api/movies/<int:movie_id>/watched", methods=["PATCH"])
def api_mark_watched(movie_id):
    movie = db.mark_watched(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify(movie)


@app.route("/api/movies/<int:movie_id>/watchlist", methods=["PATCH"])
def api_mark_watchlist(movie_id):
    movie = db.mark_watchlist(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify(movie)


@app.route("/api/movies/<int:movie_id>/rating", methods=["PATCH"])
def api_rate_movie(movie_id):
    data = request.get_json(force=True) or {}
    rating = data.get("rating")

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "Rating must be a number from 1 to 10"}), 400

    if not (1 <= rating <= 10):
        return jsonify({"error": "Rating must be between 1 and 10"}), 400

    movie = db.rate_movie(movie_id, rating)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify(movie)


@app.route("/api/movies/<int:movie_id>", methods=["DELETE"])
def api_delete_movie(movie_id):
    db.delete_movie(movie_id)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

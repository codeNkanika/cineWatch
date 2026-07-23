"""
CineWatch — database layer.

Wraps a Postgres `movies` table with a small set of CRUD functions used by
server.py. Connection details come from environment variables (see
setup.md), falling back to sane local-dev defaults.

A connection is opened lazily and re-opened automatically if it drops, so
the API server doesn't need to worry about connection lifecycle at all —
every helper just calls `_cursor()`.
"""

import os
import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

DB_CONFIG = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    database=os.environ.get("DB_NAME", "cineWatch"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", "2602"),
    port=os.environ.get("DB_PORT", "5432"),
)

_connection = None


def get_connection():
    """Returns a live connection, reconnecting if needed."""
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(**DB_CONFIG)
        _connection.autocommit = False
    return _connection


def _cursor():
    conn = get_connection()
    return conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db():
    """Creates the movies table if it doesn't exist yet, and adds any
    columns a newer frontend needs (poster_url, notes) without touching
    existing rows."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            genre TEXT,
            status TEXT DEFAULT 'Watchlist',
            rating INTEGER,
            poster_url TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    for ddl in [
        "ALTER TABLE movies ADD COLUMN IF NOT EXISTS poster_url TEXT",
        "ALTER TABLE movies ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE movies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
    ]:
        cur.execute(ddl)
    conn.commit()
    cur.close()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def view_movies():
    conn, cur = _cursor()
    cur.execute("SELECT * FROM movies ORDER BY created_at DESC, id DESC")
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_movie(movie_id):
    conn, cur = _cursor()
    cur.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def add_movie(title, genre, poster_url=None, notes=None):
    conn, cur = _cursor()
    cur.execute(
        """
        INSERT INTO movies (title, genre, status, poster_url, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (title, genre, "Watchlist", poster_url, notes),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return dict(row)


def mark_watched(movie_id):
    conn, cur = _cursor()
    cur.execute(
        "UPDATE movies SET status = 'Watched' WHERE id = %s RETURNING *",
        (movie_id,),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return dict(row) if row else None


def mark_watchlist(movie_id):
    conn, cur = _cursor()
    cur.execute(
        "UPDATE movies SET status = 'Watchlist' WHERE id = %s RETURNING *",
        (movie_id,),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return dict(row) if row else None


def rate_movie(movie_id, rating):
    conn, cur = _cursor()
    cur.execute(
        "UPDATE movies SET rating = %s WHERE id = %s RETURNING *",
        (rating, movie_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return dict(row) if row else None


def delete_movie(movie_id):
    conn, cur = _cursor()
    cur.execute("DELETE FROM movies WHERE id = %s", (movie_id,))
    conn.commit()
    cur.close()

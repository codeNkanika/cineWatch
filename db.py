"""
db.py
-----
Everything related to talking to PostgreSQL lives here, so server.py
never has to know about connection strings, cursors, or SQL.

Uses a small threaded connection pool so the Flask dev server (and any
future production WSGI server) can handle multiple requests without
opening a fresh TCP connection to Postgres every time.
"""

import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

load_dotenv()

# Hosted Postgres providers (Render, Railway, Heroku, etc.) give you a single
# connection string via DATABASE_URL instead of separate host/user/password
# fields. Support both so the same code runs locally and in production.
DATABASE_URL = os.getenv("DATABASE_URL")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "cozy_watchlist"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

_pool = None


def init_pool(minconn=1, maxconn=10):
    """Create the connection pool once, at app startup."""
    global _pool
    if _pool is None:
        if DATABASE_URL:
            # Render's free Postgres (and some others) only accept SSL
            _pool = ThreadedConnectionPool(minconn, maxconn, dsn=DATABASE_URL, sslmode="require")
        else:
            _pool = ThreadedConnectionPool(minconn, maxconn, **DB_CONFIG)
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_cursor(commit=False):
    """
    Context manager that hands back a dict-cursor from the pool and
    always returns the connection when it's done, even on error.

        with get_cursor(commit=True) as cur:
            cur.execute("INSERT INTO ...")
    """
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        _pool.putconn(conn)


def init_db():
    """Create the watchlist table if it doesn't exist yet. Safe to re-run."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist_items (
                id          SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                media_type  TEXT NOT NULL DEFAULT 'movie'
                            CHECK (media_type IN ('movie', 'tv')),
                status      TEXT NOT NULL DEFAULT 'want_to_watch'
                            CHECK (status IN ('want_to_watch', 'watching', 'watched')),
                rating      SMALLINT
                            CHECK (rating BETWEEN 1 AND 5),
                notes       TEXT DEFAULT '',
                added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )


# ---------------------------------------------------------------------
# Queries used by the API layer (server.py)
# ---------------------------------------------------------------------

def list_items(status=None):
    with get_cursor() as cur:
        if status:
            cur.execute(
                "SELECT * FROM watchlist_items WHERE status = %s ORDER BY added_at DESC;",
                (status,),
            )
        else:
            cur.execute("SELECT * FROM watchlist_items ORDER BY added_at DESC;")
        return cur.fetchall()


def get_item(item_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM watchlist_items WHERE id = %s;", (item_id,))
        return cur.fetchone()


def create_item(title, media_type, notes=""):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO watchlist_items (title, media_type, notes)
            VALUES (%s, %s, %s)
            RETURNING *;
            """,
            (title, media_type, notes),
        )
        return cur.fetchone()


def update_item(item_id, **fields):
    """
    Partial update. Only columns present in `fields` get touched.
    Allowed keys: title, media_type, status, rating, notes
    """
    allowed = {"title", "media_type", "status", "rating", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_item(item_id)

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [item_id]

    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE watchlist_items SET {set_clause} WHERE id = %s RETURNING *;",
            values,
        )
        return cur.fetchone()


def delete_item(item_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM watchlist_items WHERE id = %s RETURNING id;", (item_id,))
        return cur.fetchone()


def get_stats():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'want_to_watch') AS want_to_watch,
                COUNT(*) FILTER (WHERE status = 'watching')      AS watching,
                COUNT(*) FILTER (WHERE status = 'watched')       AS watched,
                COUNT(*)                                          AS total
            FROM watchlist_items;
            """
        )
        return cur.fetchone()

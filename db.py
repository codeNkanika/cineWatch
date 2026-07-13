import os
import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
# Uses environment variables when available (recommended for deployment),
# falling back to the original local defaults for local dev.

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "cineWatch"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "2602"),
        port=os.environ.get("DB_PORT", "5432"),
    )


connection = get_connection()
connection.autocommit = False


def _cursor():
    return connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db():
    """Creates the movies table if it doesn't exist yet, and adds any
    columns the newer frontend needs (poster_url, notes) without touching
    existing rows."""
    cur = connection.cursor()
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
    # Backfill columns for anyone running against an older table.
    for col, ddl in [
        ("poster_url", "ALTER TABLE movies ADD COLUMN IF NOT EXISTS poster_url TEXT"),
        ("notes", "ALTER TABLE movies ADD COLUMN IF NOT EXISTS notes TEXT"),
        ("created_at", "ALTER TABLE movies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"),
    ]:
        cur.execute(ddl)
    connection.commit()
    cur.close()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def view_movies():
    cur = _cursor()
    cur.execute("SELECT * FROM movies ORDER BY created_at DESC, id DESC")
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_movie(movie_id):
    cur = _cursor()
    cur.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def add_movie(title, genre, poster_url=None, notes=None):
    cur = _cursor()
    cur.execute(
        """
        INSERT INTO movies (title, genre, status, poster_url, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (title, genre, "Watchlist", poster_url, notes),
    )
    row = cur.fetchone()
    connection.commit()
    cur.close()
    return dict(row)


def mark_watched(movie_id):
    cur = _cursor()
    cur.execute(
        "UPDATE movies SET status = 'Watched' WHERE id = %s RETURNING *",
        (movie_id,),
    )
    row = cur.fetchone()
    connection.commit()
    cur.close()
    return dict(row) if row else None


def mark_watchlist(movie_id):
    cur = _cursor()
    cur.execute(
        "UPDATE movies SET status = 'Watchlist' WHERE id = %s RETURNING *",
        (movie_id,),
    )
    row = cur.fetchone()
    connection.commit()
    cur.close()
    return dict(row) if row else None


def rate_movie(movie_id, rating):
    cur = _cursor()
    cur.execute(
        "UPDATE movies SET rating = %s WHERE id = %s RETURNING *",
        (rating, movie_id),
    )
    row = cur.fetchone()
    connection.commit()
    cur.close()
    return dict(row) if row else None


def delete_movie(movie_id):
    cur = _cursor()
    cur.execute("DELETE FROM movies WHERE id = %s", (movie_id,))
    connection.commit()
    cur.close()

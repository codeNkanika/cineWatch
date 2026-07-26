-- Cozy Watchlist schema
-- This runs automatically when you start server.py (see db.init_db()),
-- but you can also run it by hand with:
--   psql -U postgres -d cozy_watchlist -f schema.sql
 
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
 
CREATE TABLE IF NOT EXISTS watchlist_items (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
 
CREATE INDEX IF NOT EXISTS idx_watchlist_items_user_id ON watchlist_items(user_id);
 

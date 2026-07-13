# CineWatch — Setup

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

This installs `psycopg2-binary` (already used by your `db.py`) plus `flask`
and `flask-cors`, which are needed to serve the new frontend and expose your
database functions over HTTP.

## 2. Configure the database connection

`db.py` now reads connection details from environment variables, falling
back to your original local defaults (`localhost`, database `cineWatch`,
user `postgres`, password `2602`) if none are set. To override, either
export variables before running:

```bash
export DB_HOST=localhost
export DB_NAME=cineWatch
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_PORT=5432
```

or just leave it as-is if your local Postgres matches the defaults.

Make sure Postgres is running and the `cineWatch` database exists:

```bash
createdb cineWatch
```

You don't need to create the `movies` table by hand — `server.py` calls
`db.init_db()` on startup, which creates the table if it's missing and adds
the `poster_url` / `notes` columns if you already have an older table from
before.

## 3. Run the app

```bash
python server.py
```

Then open **http://localhost:5000** in your browser. That's it — one
process serves both the API and the frontend.

## 4. What changed from the original files

- **`db.py`** — same five functions your teacher already saw
  (`add_movie`, `view_movies`, `mark_watched`, `rate_movie`, `delete_movie`),
  plus `get_movie`, `mark_watchlist`, and an `init_db()` helper. Also added
  optional `poster_url` and `notes` columns so the UI has something to show
  besides title/genre.
- **`app.py`** — untouched. Your original terminal menu still works exactly
  as before, independent of the web app.
- **`server.py`** — new. A small Flask file whose routes just call the
  functions in `db.py` and return JSON, plus two routes that serve the
  frontend files.
- **`templates/index.html`, `static/css/style.css`, `static/js/app.js`** —
  new. The actual frontend.

## 5. Project structure

```
cinewatch/
├── app.py              # original CLI, unchanged
├── db.py                # database functions (extended)
├── server.py            # NEW — Flask API + serves frontend
├── requirements.txt
├── setup.md
├── templates/
│   └── index.html        # NEW — page shell
└── static/
    ├── css/
    │   └── style.css      # NEW — all styling
    └── js/
        └── app.js         # NEW — fetches API, renders UI
```

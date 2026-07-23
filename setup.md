# CineWatch — Setup

A cozy movie wishlist & ledger, styled as a book of cinema ticket stubs.

## 1. Install dependencies

```bash
cd cinewatch
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

This installs `Flask`, `flask-cors`, and `psycopg2-binary`.

## 2. Configure the database connection

`db.py` reads connection details from environment variables, falling back
to local defaults (`localhost`, database `cineWatch`, user `postgres`,
password `2602`, port `5432`) if none are set. To override, export
variables before running:

```bash
export DB_HOST=localhost
export DB_NAME=cineWatch
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_PORT=5432
```

Make sure Postgres is running and the database exists:

```bash
createdb cineWatch
```

You don't need to create the `movies` table by hand — `server.py` calls
`db.init_db()` on startup, which creates the table if it's missing and
backfills the `poster_url` / `notes` / `created_at` columns on older tables.

## 3. Run the app

```bash
python server.py
```

Then open **http://localhost:5000**. One process serves both the API and
the frontend.

## 4. Project structure

```
cinewatch/
├── db.py                  # database functions (add/view/mark/rate/delete + init_db)
├── server.py               # Flask API + serves the frontend
├── requirements.txt
├── setup.md
├── templates/
│   └── index.html            # page shell (marquee header, box-office hero, ticket grid, modal)
└── static/
    ├── css/
    │   └── style.css          # full design system — theater/ticket-stub theme
    └── js/
        └── app.js             # fetches the API, renders cards, handles all interactions
```

## 5. API reference

| Method | Route                        | Body                    | Description                    |
|--------|-------------------------------|--------------------------|---------------------------------|
| GET    | `/api/movies`                 | —                        | List all movies                |
| GET    | `/api/movies/<id>`             | —                        | Get one movie                  |
| POST   | `/api/movies`                  | `title, genre, poster_url, notes` | Add a movie (status: Watchlist) |
| PATCH  | `/api/movies/<id>/watched`      | —                        | Mark as watched                |
| PATCH  | `/api/movies/<id>/watchlist`    | —                        | Move back to watchlist         |
| PATCH  | `/api/movies/<id>/rating`       | `rating` (1–10)          | Set a rating                   |
| DELETE | `/api/movies/<id>`              | —                        | Remove a movie                 |

## 6. Design notes

The whole UI leans into the idea of a "ledger of ticket stubs": each film
card is die-cut like a real admission ticket (perforated tear line, notch
cutouts), the header is a lightbulb marquee, and the stats up top are
printed as a shared admission strip. Fonts: **Fraunces** (display/italic),
**Inter** (body), **Space Mono** (ticket data — codes, counts, labels).

> Note: your original `app.py` command-line tool wasn't part of this
> upload, so it isn't included here — everything else (`db.py`'s five
> core functions, `server.py`, and the frontend) has been rebuilt and
> restyled from your files.

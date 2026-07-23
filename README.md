# 🕯️ Cozy Watchlist

A small, warm little app for keeping track of the movies and shows you want
to watch — no algorithms, no infinite scroll, just a list that feels like
your own reading nook.

Full-stack project: **HTML/CSS/JS frontend → Flask REST API → PostgreSQL.**

## Features

- Add movies or TV shows with an optional note
- Move items through **Want to watch → Watching → Watched**
- Rate anything you've finished, 1–5 stars
- Filter your list by status
- Live counts for each status
- Ticket-stub card design, warm lamplight color palette, small hero animation

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Vanilla HTML, CSS, JavaScript (no build step, no frameworks) |
| Backend | Python, Flask, Flask-CORS |
| Database | PostgreSQL via `psycopg2` (pooled connections) |

## Project structure

```
watchlist-app/
├── index.html        # Landing page
├── watchlist.html     # Main app page
├── style.css          # Shared cozy stylesheet
├── app.js             # Frontend logic — talks to the API
├── server.py           # Flask app: routes + REST API
├── db.py                # PostgreSQL connection pool + queries
├── schema.sql            # Reference SQL schema (auto-applied by db.py too)
├── requirements.txt       # Python dependencies
├── .env.example            # Environment variable template
└── setup.md                 # Full setup walkthrough
```

## Quick start

See **[setup.md](setup.md)** for the full step-by-step guide (Postgres, VS
Code, running the app, and pushing to GitHub). Want a real public URL
instead of running it locally? See **[DEPLOY.md](DEPLOY.md)** — GitHub Pages
can't run this (it only hosts static files), so that guide walks through
deploying to Render instead, which is free and supports both the app and
the database. The short version for running locally:

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Postgres credentials
python server.py
```

Then open `http://localhost:5000`.

## API reference

All endpoints are under `/api`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/items` | List all items (optional `?status=` filter) |
| `POST` | `/api/items` | Add a new item — body: `{ title, media_type, notes }` |
| `PATCH` | `/api/items/<id>` | Update any subset of `title`, `media_type`, `status`, `rating`, `notes` |
| `DELETE` | `/api/items/<id>` | Remove an item |
| `GET` | `/api/stats` | Counts per status |

`media_type` is `"movie"` or `"tv"`. `status` is one of `"want_to_watch"`,
`"watching"`, `"watched"`. `rating` is `1`–`5` or `null`.

## Notes

- The database table is created automatically the first time you run
  `python server.py` — no manual migration step needed.
- `.env` holds your local database credentials and is git-ignored.

# Setup guide

Everything you need to get Cozy Watchlist running locally in VS Code, talking
to a real PostgreSQL database, and pushed up to GitHub.

## 0. What you'll need installed

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/) (14+ is fine)
- [VS Code](https://code.visualstudio.com/)
- [Git](https://git-scm.com/downloads)
- VS Code extensions (optional but nice): **Python** (Microsoft) and
  **PostgreSQL** (by Chris Kolkman, adds a database explorer in the sidebar)

---

## 1. Create the database

Open a terminal (or VS Code's integrated terminal, `` Ctrl+` ``) and run:

```bash
# log into the default postgres superuser
psql -U postgres
```

Inside the `psql` prompt:

```sql
CREATE DATABASE cozy_watchlist;
\q
```

That's it — the table itself gets created automatically the first time you
run the server (see `db.py`'s `init_db()`), so you don't need to run
`schema.sql` by hand unless you want to.

---

## 2. Open the project in VS Code

```bash
cd watchlist-app
code .
```

---

## 3. Create a virtual environment and install dependencies

In the VS Code terminal:

```bash
python -m venv venv

# activate it
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows (PowerShell: venv\Scripts\Activate.ps1)

pip install -r requirements.txt
```

VS Code may prompt "Select a Python interpreter" — pick the one inside
`venv/`.

---

## 4. Configure your environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your real Postgres credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cozy_watchlist
DB_USER=postgres
DB_PASSWORD=your_actual_password
PORT=5000
```

`.env` is already listed in `.gitignore`, so your password never gets
committed.

---

## 5. Run it

```bash
python server.py
```

You should see:

```
🕯️  Cozy Watchlist running at http://localhost:5000
```

Open that URL in your browser. The landing page is at `/`, the app itself
is at `/watchlist`. The first request will auto-create the
`watchlist_items` table if it doesn't already exist.

**Quick check the API is alive:** visit `http://localhost:5000/api/health` —
you should see `{"status": "ok"}`.

---

## 6. Everyday development

- Backend code: `server.py` (routes) and `db.py` (all SQL/database logic)
- Frontend code: `index.html`, `watchlist.html`, `style.css`, `app.js`
- Flask runs with `debug=True`, so editing `server.py` or `db.py` auto-reloads
  the server. For frontend files, just refresh the browser.

---

## 7. Push this project to GitHub

If you haven't already, create a free account at
[github.com](https://github.com) and install Git.

**Option A — using the GitHub website + git CLI:**

1. Go to [github.com/new](https://github.com/new), name the repo (e.g.
   `cozy-watchlist`), leave it empty (no README/gitignore — you already have
   those), and click **Create repository**.
2. Back in your terminal, inside the `watchlist-app` folder:

```bash
git init
git add .
git commit -m "Initial commit: cozy watchlist app"
git branch -M main
git remote add origin https://github.com/<your-username>/cozy-watchlist.git
git push -u origin main
```

**Option B — using the GitHub CLI (`gh`):**

```bash
gh auth login
git init
git add .
git commit -m "Initial commit: cozy watchlist app"
gh repo create cozy-watchlist --public --source=. --remote=origin --push
```

**Option C — using VS Code's built-in Source Control:**

1. Click the Source Control icon in the left sidebar (or `Ctrl+Shift+G`).
2. Click **Initialize Repository**.
3. Stage and commit your files with a message like "Initial commit."
4. Click **Publish Branch** and follow the prompts to create the GitHub repo
   directly from VS Code.

---

## Troubleshooting

| Problem | Likely fix |
|---|---|
| `psycopg2.OperationalError: connection refused` | PostgreSQL isn't running. Start it (`brew services start postgresql`, `sudo service postgresql start`, or via the Postgres app on Windows). |
| `FATAL: password authentication failed` | Double-check `DB_USER` / `DB_PASSWORD` in `.env` match your local Postgres setup. |
| `relation "watchlist_items" does not exist` | Restart `server.py` — `init_db()` runs on startup and creates it. |
| Port 5000 already in use | Change `PORT` in `.env` to something like `5050`. |
| CSS/JS changes not showing | Hard-refresh the browser (`Ctrl+Shift+R` / `Cmd+Shift+R`) — static files can be cached. |

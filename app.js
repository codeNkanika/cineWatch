/* =========================================================
   app.js — frontend logic for watchlist.html
   Talks to the Flask API (server.py) which is backed by
   PostgreSQL (db.py). No frameworks, just fetch + DOM.
   ========================================================= */

const API_BASE = "/api";

const state = {
  items: [],
  filter: "all",
};

// ---------------- DOM refs ----------------
const grid = document.getElementById("grid");
const emptyState = document.getElementById("empty");
const addForm = document.getElementById("add-form");
const titleInput = document.getElementById("title-input");
const notesInput = document.getElementById("notes-input");
const filterBar = document.getElementById("filters");
const toastEl = document.getElementById("toast");

const statWant = document.getElementById("stat-want");
const statWatching = document.getElementById("stat-watching");
const statWatched = document.getElementById("stat-watched");

const STATUS_LABEL = {
  want_to_watch: "Want to watch",
  watching: "Watching",
  watched: "Watched",
};

// ---------------- API helpers ----------------

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed`);
  return res.json();
}

async function apiSend(path, method, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `${method} ${path} failed`);
  }
  return res.json();
}

// ---------------- Data flow ----------------

async function loadEverything() {
  try {
    const [items, stats] = await Promise.all([
      apiGet("/items"),
      apiGet("/stats"),
    ]);
    state.items = items;
    renderStats(stats);
    renderGrid();
  } catch (err) {
    showToast("Couldn't reach the server — is it running?");
    console.error(err);
  }
}

async function addItem(evt) {
  evt.preventDefault();
  const title = titleInput.value.trim();
  if (!title) return;

  const media_type = document.querySelector('input[name="media_type"]:checked').value;
  const notes = notesInput.value.trim();

  try {
    await apiSend("/items", "POST", { title, media_type, notes });
    titleInput.value = "";
    notesInput.value = "";
    titleInput.focus();
    showToast(`Added "${title}"`);
    await loadEverything();
  } catch (err) {
    showToast(err.message);
  }
}

async function changeStatus(id, status) {
  try {
    await apiSend(`/items/${id}`, "PATCH", { status });
    await loadEverything();
  } catch (err) {
    showToast(err.message);
  }
}

async function setRating(id, rating) {
  try {
    await apiSend(`/items/${id}`, "PATCH", { rating });
    await loadEverything();
  } catch (err) {
    showToast(err.message);
  }
}

async function removeItem(id, title) {
  if (!confirm(`Remove "${title}" from your list?`)) return;
  try {
    await apiSend(`/items/${id}`, "DELETE");
    showToast(`Removed "${title}"`);
    await loadEverything();
  } catch (err) {
    showToast(err.message);
  }
}

// ---------------- Rendering ----------------

function renderStats(stats) {
  statWant.textContent = stats.want_to_watch ?? 0;
  statWatching.textContent = stats.watching ?? 0;
  statWatched.textContent = stats.watched ?? 0;
}

function renderGrid() {
  const visible = state.items.filter(
    (item) => state.filter === "all" || item.status === state.filter
  );

  grid.innerHTML = "";

  if (visible.length === 0) {
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";

  visible.forEach((item) => grid.appendChild(renderTicket(item)));
}

function renderTicket(item) {
  const card = document.createElement("article");
  card.className = `ticket ticket--${item.status.replace("want_to_watch", "want")}`;

  const typeLabel = item.media_type === "tv" ? "TV Show" : "Movie";
  const typeClass = item.media_type === "tv" ? "ticket__type--tv" : "ticket__type--movie";

  card.innerHTML = `
    <div class="ticket__main">
      <div class="ticket__top">
        <span class="ticket__type ${typeClass}">${typeLabel}</span>
      </div>
      <h3 class="ticket__title"></h3>
      ${item.notes ? `<p class="ticket__notes"></p>` : ""}
      <div class="ticket__rating" data-id="${item.id}">
        ${[1, 2, 3, 4, 5]
          .map(
            (n) =>
              `<span class="star ${item.rating >= n ? "filled" : ""}" data-value="${n}">★</span>`
          )
          .join("")}
      </div>
    </div>
    <div class="ticket__perf"></div>
    <div class="ticket__foot">
      <select class="status-select">
        ${Object.entries(STATUS_LABEL)
          .map(
            ([value, label]) =>
              `<option value="${value}" ${item.status === value ? "selected" : ""}>${label}</option>`
          )
          .join("")}
      </select>
      <button class="ticket__delete" title="Remove">🗑</button>
    </div>
  `;

  // Set text via textContent to avoid any HTML injection from titles/notes
  card.querySelector(".ticket__title").textContent = item.title;
  if (item.notes) card.querySelector(".ticket__notes").textContent = item.notes;

  // Wire up interactions
  card.querySelectorAll(".star").forEach((star) => {
    star.addEventListener("click", () => {
      const value = Number(star.dataset.value);
      const alreadyThatRating = item.rating === value;
      setRating(item.id, alreadyThatRating ? null : value);
    });
  });

  card.querySelector(".status-select").addEventListener("change", (e) => {
    changeStatus(item.id, e.target.value);
  });

  card.querySelector(".ticket__delete").addEventListener("click", () => {
    removeItem(item.id, item.title);
  });

  return card;
}

// ---------------- Toast ----------------

let toastTimer = null;
function showToast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2600);
}

// ---------------- Filters ----------------

filterBar.addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-tab");
  if (!btn) return;
  filterBar.querySelectorAll(".filter-tab").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  state.filter = btn.dataset.filter;
  renderGrid();
});

// ---------------- Init ----------------

addForm.addEventListener("submit", addItem);
loadEverything();

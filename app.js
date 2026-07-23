/* ==========================================================================
   CineWatch — frontend logic
   Talks to the Flask API (server.py) which wraps db.py.
   ========================================================================== */

const API_BASE = "/api/movies";

const state = {
  movies: [],
  filter: "all",
  search: "",
  sort: "recent",
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------

const filmGrid = document.getElementById("filmGrid");
const emptyState = document.getElementById("emptyState");
const emptyMsg = document.getElementById("emptyMsg");
const searchInput = document.getElementById("searchInput");
const sortSelect = document.getElementById("sortSelect");
const tabs = document.querySelectorAll(".tab");

const modalOverlay = document.getElementById("modalOverlay");
const movieForm = document.getElementById("movieForm");
const formError = document.getElementById("formError");
const toastEl = document.getElementById("toast");

const statTotal = document.getElementById("statTotal");
const statWatched = document.getElementById("statWatched");
const statAvg = document.getElementById("statAvg");
const tickerTrack = document.getElementById("tickerTrack");

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiRequest(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

async function fetchMovies() {
  state.movies = await apiRequest(API_BASE);
  render();
}

async function createMovie(payload) {
  const movie = await apiRequest(API_BASE, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.movies.unshift(movie);
  render();
  showToast(`Added "${movie.title}" to your ledger`);
}

async function setWatched(id, watched) {
  const path = `${API_BASE}/${id}/${watched ? "watched" : "watchlist"}`;
  const updated = await apiRequest(path, { method: "PATCH" });
  patchMovie(updated);
  showToast(watched ? "Stamped as watched" : "Moved back to watchlist");
}

async function setRating(id, rating) {
  const updated = await apiRequest(`${API_BASE}/${id}/rating`, {
    method: "PATCH",
    body: JSON.stringify({ rating }),
  });
  patchMovie(updated);
  showToast(`Rated ${updated.title} — ${rating}/10`);
}

async function removeMovie(id) {
  await apiRequest(`${API_BASE}/${id}`, { method: "DELETE" });
  state.movies = state.movies.filter((m) => m.id !== id);
  render();
  showToast("Torn from the ledger");
}

function patchMovie(updated) {
  const idx = state.movies.findIndex((m) => m.id === updated.id);
  if (idx !== -1) state.movies[idx] = updated;
  render();
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function getFiltered() {
  let list = [...state.movies];

  if (state.filter !== "all") {
    list = list.filter((m) => m.status === state.filter);
  }

  if (state.search.trim()) {
    const q = state.search.trim().toLowerCase();
    list = list.filter(
      (m) =>
        m.title?.toLowerCase().includes(q) ||
        m.genre?.toLowerCase().includes(q)
    );
  }

  if (state.sort === "title") {
    list.sort((a, b) => a.title.localeCompare(b.title));
  } else if (state.sort === "rating") {
    list.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  }
  // "recent" relies on API's default order (created_at desc)

  return list;
}

function render() {
  const list = getFiltered();

  filmGrid.innerHTML = "";
  emptyState.hidden = list.length !== 0;

  if (state.movies.length === 0) {
    emptyMsg.textContent = "Nothing here yet — add the first film to start your ledger.";
  } else if (list.length === 0) {
    emptyMsg.textContent = "No films match this search or filter.";
  }

  list.forEach((movie, i) => {
    filmGrid.appendChild(buildCard(movie, i));
  });

  renderStats();
  renderTicker();
}

function renderTicker() {
  const titles = state.movies.length
    ? state.movies.map((m) => m.title)
    : ["Add your first film to see it here"];
  // duplicate the list so the CSS scroll (translateX -50%) loops seamlessly
  const loop = [...titles, ...titles];
  tickerTrack.innerHTML = loop.map((t) => `<span>${escapeHTML(t)}</span>`).join("");
}

function renderStats() {
  const total = state.movies.length;
  const watched = state.movies.filter((m) => m.status === "Watched").length;
  const rated = state.movies.filter((m) => typeof m.rating === "number" && m.rating !== null);
  const avg = rated.length
    ? (rated.reduce((sum, m) => sum + m.rating, 0) / rated.length).toFixed(1)
    : "–";

  statTotal.textContent = total;
  statWatched.textContent = watched;
  statAvg.textContent = avg;
}

function buildCard(movie, index) {
  const card = document.createElement("article");
  card.className = "film-card";
  card.style.animationDelay = `${Math.min(index * 35, 300)}ms`;

  const isWatched = movie.status === "Watched";

  card.innerHTML = `
    <div class="poster-frame">
      ${
        movie.poster_url
          ? `<img src="${escapeAttr(movie.poster_url)}" alt="${escapeAttr(movie.title)} poster" loading="lazy" onerror="this.outerHTML=fallbackPosterHTML()" />`
          : fallbackPosterHTML()
      }
      <span class="status-chip ${isWatched ? "watched" : "watchlist"}">${isWatched ? "Watched" : "To watch"}</span>
      ${movie.rating ? `<span class="rating-badge">${movie.rating}</span>` : ""}
      ${posterScrimHTML(movie)}
    </div>
    <div class="perf-seam" aria-hidden="true"></div>
    <div class="stub-footer">
      ${movie.notes ? `<p class="card-notes">${escapeHTML(movie.notes)}</p>` : ""}
      <div class="card-actions">
        <button class="icon-btn watch-toggle ${isWatched ? "active-state" : ""}" data-id="${movie.id}" data-watched="${isWatched}">
          ${watchIcon(isWatched)} ${isWatched ? "Watched" : "Mark seen"}
        </button>
        <button class="icon-btn rate-btn" data-id="${movie.id}">
          ${starIcon()} Rate
        </button>
        <button class="icon-btn danger delete-btn" data-id="${movie.id}" aria-label="Remove ${escapeAttr(movie.title)}">
          ${trashIcon()}
        </button>
      </div>
    </div>
  `;

  card.querySelector(".watch-toggle").addEventListener("click", (e) => {
    const btn = e.currentTarget;
    const willBeWatched = btn.dataset.watched !== "true";
    setWatched(movie.id, willBeWatched).catch((err) => showToast(err.message, true));
  });

  card.querySelector(".rate-btn").addEventListener("click", (e) => {
    openRatingPopover(e.currentTarget, movie);
  });

  card.querySelector(".delete-btn").addEventListener("click", () => {
    if (confirm(`Remove "${movie.title}" from your ledger?`)) {
      removeMovie(movie.id).catch((err) => showToast(err.message, true));
    }
  });

  return card;
}

function posterScrimHTML(movie) {
  return `<div class="poster-scrim">
    <h3 class="card-title">${escapeHTML(movie.title)}</h3>
    <p class="card-genre">${escapeHTML(movie.genre || "Unsorted")}</p>
  </div>`;
}

function fallbackPosterHTML() {
  return `<div class="poster-fallback">
    <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
      <rect x="4" y="6" width="26" height="22" rx="2" stroke="currentColor" stroke-width="1.4"/>
      <path d="M4 12H30" stroke="currentColor" stroke-width="1.4"/>
      <path d="M9 6V12M14 6V12M19 6V12M24 6V12" stroke="currentColor" stroke-width="1.4"/>
      <path d="M13 17L21 21L13 25V17Z" fill="currentColor"/>
    </svg>
  </div>`;
}
window.fallbackPosterHTML = fallbackPosterHTML;

function watchIcon(active) {
  return `<svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M2 6.5L5 9.5L11 3.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}
function starIcon() {
  return `<svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M6.5 1L8.1 4.6L12 5.1L9.2 7.7L9.9 11.5L6.5 9.6L3.1 11.5L3.8 7.7L1 5.1L4.9 4.6L6.5 1Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>`;
}
function trashIcon() {
  return `<svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M2.5 3.5H10.5M5 3.5V2C5 1.5 5.4 1 6 1H7C7.6 1 8 1.5 8 2V3.5M9.5 3.5L9 11C9 11.5 8.6 12 8 12H5C4.4 12 4 11.5 4 11L3.5 3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

// ---------------------------------------------------------------------------
// Rating popover
// ---------------------------------------------------------------------------

let activePopover = null;

function openRatingPopover(anchorBtn, movie) {
  closePopover();

  const pop = document.createElement("div");
  pop.className = "rating-pop";
  for (let i = 1; i <= 10; i++) {
    const b = document.createElement("button");
    b.textContent = i;
    if (movie.rating === i) b.classList.add("selected");
    b.addEventListener("click", () => {
      setRating(movie.id, i).catch((err) => showToast(err.message, true));
      closePopover();
    });
    pop.appendChild(b);
  }

  document.body.appendChild(pop);
  const rect = anchorBtn.getBoundingClientRect();
  pop.style.top = `${window.scrollY + rect.bottom + 8}px`;
  pop.style.left = `${Math.min(window.scrollX + rect.left - 60, window.innerWidth - 280)}px`;

  activePopover = pop;

  setTimeout(() => {
    document.addEventListener("click", handleOutsideClick);
  }, 0);
}

function handleOutsideClick(e) {
  if (activePopover && !activePopover.contains(e.target)) {
    closePopover();
  }
}

function closePopover() {
  if (activePopover) {
    activePopover.remove();
    activePopover = null;
    document.removeEventListener("click", handleOutsideClick);
  }
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

function openModal() {
  modalOverlay.hidden = false;
  formError.hidden = true;
  movieForm.reset();
  document.getElementById("fieldTitle").focus();
}
function closeModal() {
  modalOverlay.hidden = true;
}

document.getElementById("openAddModal").addEventListener("click", openModal);
document.getElementById("closeModal").addEventListener("click", closeModal);
document.getElementById("cancelModal").addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modalOverlay.hidden) closeModal();
});

movieForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("fieldTitle").value.trim();
  const genre = document.getElementById("fieldGenre").value.trim();
  const poster_url = document.getElementById("fieldPoster").value.trim();
  const notes = document.getElementById("fieldNotes").value.trim();

  if (!title) {
    formError.textContent = "Title is required.";
    formError.hidden = false;
    return;
  }

  const submitBtn = movieForm.querySelector(".btn-solid");
  submitBtn.disabled = true;
  submitBtn.textContent = "Printing…";

  try {
    await createMovie({ title, genre, poster_url, notes });
    closeModal();
  } catch (err) {
    formError.textContent = err.message;
    formError.hidden = false;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Print ticket";
  }
});

// ---------------------------------------------------------------------------
// Toolbar interactions
// ---------------------------------------------------------------------------

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
    });
    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
    state.filter = tab.dataset.filter;
    render();
  });
});

let searchTimer;
searchInput.addEventListener("input", (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.search = e.target.value;
    render();
  }, 150);
});

sortSelect.addEventListener("change", (e) => {
  state.sort = e.target.value;
  render();
});

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------

let toastTimer;
function showToast(message, isError = false) {
  clearTimeout(toastTimer);
  toastEl.textContent = message;
  toastEl.style.background = isError ? "var(--danger)" : "var(--ink)";
  toastEl.classList.add("show");
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2600);
}

// ---------------------------------------------------------------------------
// Utils
// ---------------------------------------------------------------------------

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
function escapeAttr(str) {
  return (str ?? "").replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

fetchMovies().catch((err) => {
  console.error(err);
  emptyMsg.textContent = "Couldn't reach the server. Is server.py running?";
  emptyState.hidden = false;
});

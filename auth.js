/* =========================================================
   auth.js — shared logic for login.html and signup.html
   ========================================================= */

const API_BASE = "/api";

async function apiSend(path, method, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `${method} ${path} failed`);
  return data;
}

function showError(el, message) {
  el.textContent = message;
  el.classList.add("show");
}

function wireAuthForm(formId, endpoint, redirectTo) {
  const form = document.getElementById(formId);
  const errorEl = document.getElementById("auth-error");
  if (!form) return;

  form.addEventListener("submit", async (evt) => {
    evt.preventDefault();
    errorEl.classList.remove("show");

    const email = document.getElementById("email-input").value.trim();
    const password = document.getElementById("password-input").value;

    try {
      await apiSend(endpoint, "POST", { email, password });
      window.location.href = redirectTo;
    } catch (err) {
      showError(errorEl, err.message);
    }
  });
}

// If someone who's already logged in lands on /login or /signup,
// send them straight to their watchlist instead.
(async function redirectIfAlreadyLoggedIn() {
  try {
    const res = await fetch(`${API_BASE}/me`, { credentials: "same-origin" });
    const me = await res.json();
    if (me) window.location.href = "/watchlist";
  } catch {
    /* ignore — just show the form */
  }
})();

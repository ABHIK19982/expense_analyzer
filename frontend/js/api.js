/**
 * Shared API helpers. All requests send session cookies (credentials: include).
 */
const API_BASE = "/api";

function showToast(message, category = "warning") {
  const existing = document.querySelector(".ea-toast");
  if (existing) existing.remove();

  const el = document.createElement("div");
  el.className = `alert alert-${category} ea-toast`;
  el.style.cssText =
    "position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:1000;opacity:0.9;padding:12px 20px;background:#333;color:#fff;border:1px solid #666;border-radius:4px;";
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

async function apiRequest(path, options = {}) {
  const opts = {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
  };

  const response = await fetch(`${API_BASE}${path}`, opts);
  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    data = await response.json();
  }

  if (response.status === 401) {
    const detail = data?.detail || "Please login to access this page";
    if (!window.location.pathname.endsWith("login.html")) {
      showToast(detail, "warning");
      setTimeout(() => {
        window.location.href = "/login.html";
      }, 500);
    }
    const err = new Error(detail);
    err.status = 401;
    err.data = data;
    throw err;
  }

  if (!response.ok) {
    const detail =
      (typeof data?.detail === "string" && data.detail) ||
      (Array.isArray(data?.detail) && data.detail[0]?.msg) ||
      data?.message ||
      `Request failed (${response.status})`;
    const err = new Error(detail);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

async function apiGet(path) {
  return apiRequest(path, { method: "GET" });
}

async function apiPost(path, body) {
  return apiRequest(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

async function apiPostForm(path, formData) {
  return apiRequest(path, {
    method: "POST",
    body: formData,
  });
}

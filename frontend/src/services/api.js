const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api").replace(/\/+$/, "");

function formatApiError(data, status) {
  if (data?.detail) return typeof data.detail === "string" ? data.detail : formatApiError(data.detail, status);
  if (data && typeof data === "object") {
    const messages = Object.entries(data).flatMap(([field, value]) => {
      const entries = Array.isArray(value) ? value : [value];
      return entries.map((entry) => {
        if (entry && typeof entry === "object") return formatApiError(entry, status);
        return `${field === "non_field_errors" ? "" : `${field}: `}${String(entry)}`;
      });
    }).filter(Boolean);
    if (messages.length) return messages.join(" ");
  }
  return `Request failed (${status})`;
}

export async function api(path, options = {}) {
  const token = localStorage.getItem("workneuron_access");
  const headers = { ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers, body: options.body && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Unable to connect to the server. Please make sure the backend is running.");
  }
  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { detail: text }; }
  if (!response.ok) throw new Error(formatApiError(data, response.status));
  return data;
}

export const get = (path, options = {}) => api(path, { ...options, method: "GET" });
export const post = (path, body) => api(path, { method: "POST", body });
export const patch = (path, body) => api(path, { method: "PATCH", body });
export const put = (path, body) => api(path, { method: "PUT", body });
export const remove = (path) => api(path, { method: "DELETE" });

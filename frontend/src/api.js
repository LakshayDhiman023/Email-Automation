// Thin REST client for the FastAPI backend.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const API_TOKEN = import.meta.env.VITE_API_TOKEN;

async function req(path, options = {}) {
  const res = await fetch(BASE + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(API_TOKEN ? { "X-API-Token": API_TOKEN } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // stats & metrics
  stats: () => req("/stats"),
  metrics: () => req("/metrics"),

  // app settings (timezone, send windows, working days)
  getSettings: () => req("/settings"),
  updateSettings: (s) => req("/settings", { method: "PUT", body: JSON.stringify(s) }),
  listTimezones: () => req("/settings/timezones"),
  exportCsvUrl: () => {
    const token = import.meta.env.VITE_EXPORT_TOKEN;
    return BASE + "/export/outreach.csv" + (token ? `?token=${encodeURIComponent(token)}` : "");
  },

  // suppression / opt-out list
  listSuppression: () => req("/suppression"),
  addSuppression: (email, note) =>
    req("/suppression", { method: "POST", body: JSON.stringify({ email, note }) }),
  removeSuppression: (email) =>
    req(`/suppression/${encodeURIComponent(email)}`, { method: "DELETE" }),

  // templates
  listTemplates: () => req("/templates"),
  createTemplate: (t) => req("/templates", { method: "POST", body: JSON.stringify(t) }),
  updateTemplate: (id, t) =>
    req(`/templates/${id}`, { method: "PUT", body: JSON.stringify(t) }),

  // contacts / sends
  addContact: (c) => req("/contacts", { method: "POST", body: JSON.stringify(c) }),
  listSends: (status) => req("/sends" + (status ? `?status=${status}` : "")),
  editSend: (id, patch) =>
    req(`/sends/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  approveSend: (id) => req(`/sends/${id}/approve`, { method: "POST" }),
  cancelSend: (id) => req(`/sends/${id}/cancel`, { method: "POST" }),
  closeThread: (id) => req(`/threads/${id}/close`, { method: "POST" }),

  // threads / replies
  listThreads: (status) => req("/threads" + (status ? `?status=${status}` : "")),
  listReplies: (threadId) =>
    req("/replies" + (threadId ? `?thread_id=${threadId}` : "")),
  labelThread: (threadId, payload) =>
    req(`/threads/${threadId}/label`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  pollReplies: () => req("/replies/poll", { method: "POST" }),
};

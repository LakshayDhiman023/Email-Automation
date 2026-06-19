// Thin REST client for the FastAPI backend.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function req(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
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
  // templates
  listTemplates: () => req("/templates"),
  createTemplate: (t) => req("/templates", { method: "POST", body: JSON.stringify(t) }),
  updateTemplate: (id, t) =>
    req(`/templates/${id}`, { method: "PUT", body: JSON.stringify(t) }),

  // contacts / sends
  addContact: (c) => req("/contacts", { method: "POST", body: JSON.stringify(c) }),
  listSends: (status) => req("/sends" + (status ? `?status=${status}` : "")),
  approveSend: (id) => req(`/sends/${id}/approve`, { method: "POST" }),
  cancelSend: (id) => req(`/sends/${id}/cancel`, { method: "POST" }),

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

import { useState } from "react";
import { api } from "../api";
import { Button, Card, Empty, Input } from "../components/ui";

export default function Templates({ templates, onChange }) {
  const [editing, setEditing] = useState(null); // template id or "new"
  const [form, setForm] = useState({ name: "", kind: "generic", subject: "", body: "" });

  function startEdit(t) {
    setEditing(t.id);
    setForm({ name: t.name, kind: t.kind, subject: t.subject, body: t.body });
  }
  function startNew() {
    setEditing("new");
    setForm({ name: "", kind: "generic", subject: "", body: "" });
  }

  async function save() {
    if (editing === "new") await api.createTemplate(form);
    else await api.updateTemplate(editing, form);
    setEditing(null);
    onChange?.();
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <Card
      title="Templates"
      action={
        <Button variant="ghost" onClick={startNew}>
          + New
        </Button>
      }
    >
      {templates.length === 0 && <Empty>No templates yet.</Empty>}
      <div className="space-y-2">
        {templates.map((t) => (
          <div key={t.id} className="rounded-lg border border-brand-sky/30 bg-white/60 px-4 py-2.5">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-brand-ink">{t.name}</span>
                <span className="ml-2 text-xs text-brand-ink/50">{t.kind}</span>
              </div>
              <Button variant="ghost" onClick={() => startEdit(t)}>
                Edit
              </Button>
            </div>
          </div>
        ))}
      </div>

      {editing !== null && (
        <div className="mt-4 rounded-xl border border-brand-deep/30 bg-white/80 p-4 space-y-3">
          <Input label="Name" value={form.name} onChange={set("name")} />
          <Input label="Kind" value={form.kind} onChange={set("kind")} />
          <Input label="Subject" value={form.subject} onChange={set("subject")} />
          <label className="block">
            <span className="block text-sm font-medium text-brand-ink/80 mb-1">
              Body — use {"{recruiter_name}"} and {"{company}"}
            </span>
            <textarea
              className="w-full h-40 rounded-lg border border-brand-sky/50 bg-white/90 px-3 py-2 text-sm font-sans outline-none focus:border-brand-deep focus:ring-2 focus:ring-brand-deep/20"
              value={form.body}
              onChange={set("body")}
            />
          </label>
          <div className="flex gap-2">
            <Button onClick={save}>Save</Button>
            <Button variant="ghost" onClick={() => setEditing(null)}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

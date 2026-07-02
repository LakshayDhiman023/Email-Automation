import { useState } from "react";
import { api } from "../api";
import { Button, Card, Empty, Input } from "../components/ui";

// {variable} names found in subject+body — the fields this template will ask for.
function varsIn(...texts) {
  const seen = [];
  for (const t of texts)
    for (const m of (t || "").matchAll(/\{([a-zA-Z0-9_]+)\}/g))
      if (!seen.includes(m[1])) seen.push(m[1]);
  return seen;
}

export default function Templates({ templates, onChange }) {
  const [editing, setEditing] = useState(null); // template id or "new"
  const [form, setForm] = useState({ name: "", kind: "generic", subject: "", body: "" });
  const formVars = varsIn(form.subject, form.body);

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
          <div key={t.id} className="rounded-lg border border-brand-line bg-brand-panel2 hover:bg-brand-blueSoft transition px-4 py-2.5">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-brand-ink">{t.name}</span>
                <span className="ml-2 text-xs text-brand-muted">{t.kind}</span>
              </div>
              <Button variant="ghost" onClick={() => startEdit(t)}>
                Edit
              </Button>
            </div>
          </div>
        ))}
      </div>

      {editing !== null && (
        <div className="mt-4 rounded-xl border border-brand-line bg-brand-panel2 p-4 space-y-3">
          <Input label="Name" value={form.name} onChange={set("name")} />
          <Input label="Kind" value={form.kind} onChange={set("kind")} />
          <Input label="Subject" value={form.subject} onChange={set("subject")} />
          <label className="block">
            <span className="block text-sm font-medium text-brand-muted mb-1">
              Body — insert any field as {"{like_this}"}, e.g. {"{recruiter_name}"}, {"{company}"}, {"{role}"}
            </span>
            <textarea
              className="w-full h-44 rounded-xl border border-brand-line bg-brand-panel2 px-3.5 py-2.5 text-sm text-brand-ink font-sans outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/15 transition"
              value={form.body}
              onChange={set("body")}
            />
          </label>
          <div className="text-xs text-brand-muted">
            Fields you'll fill per application:{" "}
            {formVars.length ? (
              formVars.map((v) => (
                <span key={v} className="inline-block rounded bg-brand-blueSoft text-brand-blue px-1.5 py-0.5 mr-1 font-medium">
                  {v}
                </span>
              ))
            ) : (
              <span className="italic">none yet — add {"{variables}"} above</span>
            )}
          </div>
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

import { useState } from "react";
import { api } from "../api";
import { Button, Card, Empty, Input, Select } from "../components/ui";

// {variable} names found in subject+body — the fields this template will ask for.
function varsIn(...texts) {
  const seen = [];
  for (const t of texts)
    for (const m of (t || "").matchAll(/\{([a-zA-Z0-9_]+)\}/g))
      if (!seen.includes(m[1])) seen.push(m[1]);
  return seen;
}

// Known kinds so the field stays a closed set instead of free-text typos
// (e.g. "Generic" vs "generic"); "example" marks the seeded starter templates.
const KINDS = ["generic", "official_company", "startup", "example"];

export default function Templates({ templates, onChange }) {
  const [editing, setEditing] = useState(null); // template id or "new"
  const [form, setForm] = useState({
    name: "", kind: "generic", subject: "", body: "", attach_resume: true,
  });
  const formVars = varsIn(form.subject, form.body);

  function startEdit(t) {
    setEditing(t.id);
    setForm({
      name: t.name, kind: t.kind, subject: t.subject, body: t.body,
      attach_resume: t.attach_resume ?? true,
    });
  }
  function startNew() {
    setEditing("new");
    setForm({ name: "", kind: "generic", subject: "", body: "", attach_resume: true });
  }

  async function save() {
    if (editing === "new") await api.createTemplate(form);
    else await api.updateTemplate(editing, form);
    setEditing(null);
    onChange?.();
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const hasExampleTemplates = templates.some((t) => t.kind === "example");
  const hasOwnTemplates = templates.some((t) => t.kind !== "example");

  return (
    <Card
      title="Templates"
      action={
        <Button variant="ghost" onClick={startNew}>
          + New
        </Button>
      }
    >
      {hasExampleTemplates && !hasOwnTemplates && (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          The templates below are <b>starter examples</b> — edit them or create your own
          before sending real outreach.
        </div>
      )}
      {templates.length === 0 && <Empty>No templates yet.</Empty>}
      <div className="space-y-2">
        {templates.map((t) => (
          <div key={t.id} className="rounded-lg border border-brand-line bg-brand-panel2 hover:bg-brand-blueSoft transition px-4 py-2.5">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-brand-ink">{t.name}</span>
                {t.kind === "example" ? (
                  <span className="ml-2 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
                    example
                  </span>
                ) : (
                  <span className="ml-2 text-xs text-brand-muted">{t.kind}</span>
                )}
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
          <Select label="Kind" value={form.kind} onChange={set("kind")}>
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </Select>
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
          <label className="flex items-center gap-2 text-sm text-brand-ink cursor-pointer">
            <input
              type="checkbox"
              checked={form.attach_resume}
              onChange={(e) => setForm({ ...form, attach_resume: e.target.checked })}
              className="w-4 h-4 accent-brand-blue"
            />
            Attach my resume/file to emails sent with this template
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

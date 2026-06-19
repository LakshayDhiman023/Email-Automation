import { useState } from "react";
import { api } from "../api";
import { Button, Card, Input, Select, fmt } from "../components/ui";

export default function AddContact({ templates, onAdded }) {
  const [form, setForm] = useState({ name: "", company: "", email: "", template_id: "" });
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const send = await api.addContact({
        ...form,
        template_id: Number(form.template_id),
      });
      setDraft(send);
      setForm({ name: "", company: "", email: "", template_id: "" });
      onAdded?.();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Add recruiter">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
        <Input label="Recruiter name" value={form.name} onChange={set("name")} required />
        <Input label="Company" value={form.company} onChange={set("company")} required />
        <Input
          label="Email"
          type="email"
          value={form.email}
          onChange={set("email")}
          required
        />
        <Select
          label="Template"
          value={form.template_id}
          onChange={set("template_id")}
          required
        >
          <option value="">Select…</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </Select>
        <div className="sm:col-span-2 flex items-center gap-3">
          <Button type="submit" disabled={busy}>
            {busy ? "Adding…" : "Add & generate draft"}
          </Button>
          {err && <span className="text-sm text-rose-600">{err}</span>}
        </div>
      </form>

      {draft && (
        <div className="mt-5 rounded-xl border border-brand-sky/40 bg-brand-sky/10 p-4">
          <p className="text-sm text-brand-ink/70 mb-1">
            Draft queued · scheduled <b>{fmt(draft.scheduled_at)}</b> · status{" "}
            <b>{draft.status}</b> — approve it in Pending Approvals.
          </p>
          <p className="font-medium text-brand-ink">{draft.subject}</p>
          <pre className="mt-2 whitespace-pre-wrap text-sm text-brand-ink/80 font-sans">
            {draft.body}
          </pre>
        </div>
      )}
    </Card>
  );
}

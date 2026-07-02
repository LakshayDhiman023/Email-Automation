import { useMemo, useState } from "react";
import { api } from "../api";
import { useToast } from "../components/Toast";
import { Button, Card, Input, Select, fmt } from "../components/ui";

// Fill {variables} client-side so the preview is exact & instant.
function render(text, values) {
  return (text || "").replace(/\{([a-zA-Z0-9_]+)\}/g, (m, k) =>
    values[k] != null && values[k] !== "" ? values[k] : m
  );
}

// Turn a variable name into a friendly label: recruiter_name -> "Recruiter name".
function label(v) {
  return v.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export default function AddContact({ templates, onAdded }) {
  const toast = useToast();
  const [templateId, setTemplateId] = useState("");
  const [email, setEmail] = useState("");
  const [vals, setVals] = useState({}); // variable name -> value (incl. recruiter_name, company)
  const [busy, setBusy] = useState(false);
  const [queued, setQueued] = useState(null);

  const tmpl = templates.find((t) => String(t.id) === String(templateId));
  // company is core to the recruiter record (used for dedup), so always collect it
  // even if the template text doesn't reference {company}.
  const templateVars = tmpl?.variables ?? [];
  const fields = tmpl
    ? ["company", ...templateVars.filter((v) => v !== "company")]
    : [];

  const setVar = (k) => (e) => {
    setVals({ ...vals, [k]: e.target.value });
    setQueued(null);
  };

  // recruiter_name falls back to "Hiring Manager"; job_id/job_link aren't always
  // relevant (referrals, cold HR inbox), so they're optional too.
  const optional = new Set(["recruiter_name", "job_id", "job_link"]);
  const ready =
    !!tmpl && !!email && fields.every((v) => optional.has(v) || (vals[v] || "").trim());

  const preview = useMemo(() => {
    if (!tmpl) return null;
    return { subject: render(tmpl.subject, vals), body: render(tmpl.body, vals) };
  }, [tmpl, vals]);

  async function confirmQueue() {
    setBusy(true);
    try {
      // recruiter_name + company are first-class; the rest go in `variables`
      const { recruiter_name = "", company = "", ...extra } = vals;
      const send = await api.addContact({
        name: recruiter_name,
        company,
        email,
        template_id: Number(templateId),
        variables: extra,
      });
      setQueued(send);
      setVals({});
      setEmail("");
      toast("Draft queued — approve it under Outreach", "success");
      onAdded?.();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card title="1 · Recruiter details">
        <div className="grid gap-3">
          <Select
            label="Template"
            value={templateId}
            onChange={(e) => {
              setTemplateId(e.target.value);
              setVals({});
              setQueued(null);
            }}
          >
            <option value="">Select a template…</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </Select>

          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setQueued(null);
            }}
            placeholder="mohit@company.com"
          />

          {/* company + one input per variable the chosen template uses */}
          {fields.map((v) => (
            <Input
              key={v}
              label={label(v)}
              value={vals[v] || ""}
              onChange={setVar(v)}
              placeholder={v === "recruiter_name" ? "Mohit (or leave blank → Hiring Manager)" : ""}
            />
          ))}

          {!tmpl && (
            <p className="text-xs text-brand-muted">
              Pick a template — the fields it needs will appear here.
            </p>
          )}
          {tmpl && (
            <p className="text-xs text-brand-muted">
              The email updates live on the right. Nothing is sent or saved until you confirm.
            </p>
          )}
        </div>
      </Card>

      <Card title="2 · Final email preview">
        {!preview ? (
          <div className="text-sm text-brand-muted py-10 text-center">
            Fill in the details and pick a template to preview the exact email.
          </div>
        ) : (
          <div>
            <div className="rounded-xl border border-brand-line bg-brand-panel2 p-4">
              <div className="text-xs text-brand-muted">To</div>
              <div className="text-sm text-brand-ink mb-3">{email || "—"}</div>
              <div className="text-xs text-brand-muted">Subject</div>
              <div className="font-medium text-brand-ink mb-3">{preview.subject}</div>
              <div className="text-xs text-brand-muted">Body</div>
              <pre className="mt-1 whitespace-pre-wrap text-sm text-brand-ink font-sans">
                {preview.body}
              </pre>
              <div className="mt-3 text-xs text-brand-muted">
                📎 Your configured resume will be attached.
              </div>
            </div>

            <div className="mt-4 flex items-center gap-3">
              <Button onClick={confirmQueue} disabled={!ready || busy}>
                {busy ? "Queuing…" : "Looks good — queue it"}
              </Button>
              {!ready && (
                <span className="text-xs text-brand-muted">
                  Fill email and all template fields to enable.
                </span>
              )}
            </div>

            {queued && (
              <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm">
                <span className="text-emerald-700 font-medium">Queued ✓</span>{" "}
                <span className="text-brand-muted">
                  Scheduled {fmt(queued.scheduled_at)} · awaiting your approval under{" "}
                  <b>Outreach → Approvals</b>.
                </span>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

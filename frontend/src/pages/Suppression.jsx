import { useEffect, useState } from "react";
import { api } from "../api";
import { useToast } from "../components/Toast";
import { Button, Card, Empty, Input, fmt } from "../components/ui";

const REASON_STYLE = {
  manual: "text-brand-muted",
  bounced: "text-orange-600",
  negative: "text-rose-600",
  complaint: "text-rose-600",
};

export default function Suppression({ refreshKey }) {
  const toast = useToast();
  const [rows, setRows] = useState([]);
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");

  async function load() {
    try {
      setRows(await api.listSuppression());
    } catch {
      setRows([]);
    }
  }
  useEffect(() => {
    load();
  }, [refreshKey]);

  async function add(e) {
    e.preventDefault();
    try {
      await api.addSuppression(email.trim(), note.trim() || null);
      toast(`${email} will never be emailed`, "success");
      setEmail("");
      setNote("");
      await load();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  async function remove(addr) {
    try {
      await api.removeSuppression(addr);
      toast(`Removed ${addr}`, "info");
      await load();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  return (
    <div className="space-y-5">
      <Card title="Add to suppression list">
        <form onSubmit={add} className="flex flex-wrap items-end gap-3">
          <div className="w-64">
            <Input
              label="Email"
              type="email"
              required
              placeholder="contact@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <Input
              label="Note (optional)"
              placeholder="e.g. asked to stop"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
          <Button type="submit">Suppress</Button>
        </form>
        <p className="mt-3 text-xs text-brand-muted">
          Addresses here are never emailed. Bounced addresses and contacts you label
          “Negative” are added here automatically.
        </p>
      </Card>

      <Card title={`Suppressed addresses (${rows.length})`}>
        {rows.length === 0 && <Empty>No suppressed addresses.</Empty>}
        <div className="space-y-2">
          {rows.map((r) => (
            <div
              key={r.email}
              className="flex items-center justify-between rounded-xl border border-brand-line bg-brand-panel2 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="font-medium text-brand-ink truncate">{r.email}</div>
                <div className="text-xs text-brand-muted">
                  <span className={REASON_STYLE[r.reason] || "text-brand-muted"}>
                    {r.reason}
                  </span>
                  {r.note ? ` · ${r.note}` : ""} · {fmt(r.created_at)}
                </div>
              </div>
              <Button variant="ghost" onClick={() => remove(r.email)}>
                Remove
              </Button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

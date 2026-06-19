import { useEffect, useState } from "react";
import { api } from "../api";
import { Badge, Button, Card, Empty, fmt } from "../components/ui";

export default function Approvals({ refreshKey, onChange }) {
  const [sends, setSends] = useState([]);
  const [open, setOpen] = useState(null);

  async function load() {
    setSends(await api.listSends("pending_approval"));
  }
  useEffect(() => {
    load();
  }, [refreshKey]);

  async function act(id, fn) {
    await fn(id);
    await load();
    onChange?.();
  }

  return (
    <Card title={`Pending approvals (${sends.length})`}>
      {sends.length === 0 && <Empty>Nothing waiting for approval.</Empty>}
      <div className="space-y-3">
        {sends.map((s) => (
          <div key={s.id} className="rounded-xl border border-brand-sky/40 bg-white/70 p-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-brand-ink">{s.subject}</span>{" "}
                <Badge status={s.type === "followup" ? "ooo" : s.status} />
              </div>
              <div className="text-xs text-brand-ink/60">scheduled {fmt(s.scheduled_at)}</div>
            </div>
            <button
              className="mt-1 text-xs text-brand-deep underline"
              onClick={() => setOpen(open === s.id ? null : s.id)}
            >
              {open === s.id ? "Hide" : "Preview"} body
            </button>
            {open === s.id && (
              <pre className="mt-2 whitespace-pre-wrap text-sm text-brand-ink/80 font-sans">
                {s.body}
              </pre>
            )}
            <div className="mt-3 flex gap-2">
              <Button variant="success" onClick={() => act(s.id, api.approveSend)}>
                Approve
              </Button>
              <Button variant="danger" onClick={() => act(s.id, api.cancelSend)}>
                Cancel
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
